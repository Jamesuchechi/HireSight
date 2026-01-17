import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404, JsonResponse
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_POST

from apps.accounts.models import UserProfile
from .models import Resume, ResumeOptimization, ResumeRewriteDraft, ResumeSuggestion
from .forms import (
    ResumeUploadForm,
    ResumeEditForm,
    ResumeReplaceFileForm,
    BulkResumeDeleteForm,
    ResumeRewriteForm
)
from .parsers import resume_parser
from .rewriter import ResumeRewriter
from utils.helpers import convert_markdown_to_html


class UserResumeMixin:
    """Mixin to ensure user can only access their own resumes."""

    def get_queryset(self):
        """Filter queryset to current user's resumes."""
        return Resume.objects.filter(user=self.request.user)


def _get_or_create_header_profile(user):
    """Return the UserProfile used for resume headers, creating it if missing."""
    defaults = {'full_name': user.get_full_name() or user.email.split('@')[0]}
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults=defaults)
    return profile


def _build_header_text(user):
    """Build the plain-text header that AI rewrites should begin with."""
    profile = _get_or_create_header_profile(user)
    return profile.get_header_text()


class ResumeListView(LoginRequiredMixin, UserResumeMixin, ListView):
    """List all resumes for the current user."""
    model = Resume
    template_name = 'resumes/resume_list.html'
    context_object_name = 'resumes'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        """Add stats to context."""
        context = super().get_context_data(**kwargs)
        resumes = self.get_queryset()
        
        context['stats'] = {
            'total': resumes.count(),
            'parsed': resumes.filter(status='parsed').count(),
            'parsing': resumes.filter(status='parsing').count(),
            'failed': resumes.filter(status='failed').count(),
            'primary': resumes.filter(is_primary=True).first(),
        }
        
        return context


class ResumeUploadView(LoginRequiredMixin, CreateView):
    """Upload a new resume."""
    model = Resume
    form_class = ResumeUploadForm
    template_name = 'resumes/resume_upload.html'
    success_url = reverse_lazy('resumes:list')

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle successful form submission."""
        resume = form.save()

        # Start parsing
        try:
            self._parse_resume(resume)
            messages.success(
                self.request,
                f'Resume "{resume.title}" uploaded successfully! '
                f'Parsing is in progress.'
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'Resume uploaded but parsing failed: {str(e)}'
            )

        return super().form_valid(form)

    def _parse_resume(self, resume):
        """Parse resume synchronously or queue for async processing."""
        # Mark as parsing
        resume.mark_as_parsing()

        try:
            # Parse the resume
            result = resume_parser.parse_file(
                resume.file.path,
                resume.original_filename
            )

            if result.get('success'):
                resume.mark_as_parsed(result)
            else:
                error_msg = result.get('error', 'Unknown parsing error')
                resume.mark_as_failed(error_msg)

        except Exception as e:
            resume.mark_as_failed(str(e))
            raise


class ResumeDetailView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """View resume details."""
    model = Resume
    template_name = 'resumes/resume_detail.html'
    context_object_name = 'resume'

    def get_context_data(self, **kwargs):
        """Add parsed data to context."""
        context = super().get_context_data(**kwargs)
        resume = self.object

        # Format parsed data for display
        context['parsed_skills'] = resume.get_parsed_skills_list()
        context['parsed_education'] = resume.get_education_list()
        context['parsed_contact'] = resume.get_contact_info_dict()
        context['user_profile'] = _get_or_create_header_profile(self.request.user)

        return context


class ResumeEditView(LoginRequiredMixin, UserResumeMixin, UpdateView):
    """Edit resume metadata."""
    model = Resume
    form_class = ResumeEditForm
    template_name = 'resumes/resume_edit.html'
    success_url = reverse_lazy('resumes:list')

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle successful update."""
        messages.success(
            self.request,
            f'Resume "{form.instance.title}" updated successfully!'
        )
        return super().form_valid(form)


class ResumeDeleteView(LoginRequiredMixin, UserResumeMixin, DeleteView):
    """Delete a resume."""
    model = Resume
    template_name = 'resumes/resume_confirm_delete.html'
    success_url = reverse_lazy('resumes:list')

    def delete(self, request, *args, **kwargs):
        """Delete resume and show success message."""
        resume = self.get_object()
        title = resume.title
        
        result = super().delete(request, *args, **kwargs)
        
        messages.success(
            request,
            f'Resume "{title}" deleted successfully.'
        )
        return result


class ResumeDownloadView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """Download resume file."""
    model = Resume

    def get(self, request, *args, **kwargs):
        """Serve the resume file for download."""
        resume = self.get_object()

        if not resume.file:
            raise Http404("Resume file not found.")

        # Get file content
        try:
            with default_storage.open(resume.file.name, 'rb') as f:
                file_data = f.read()

            # Determine content type
            content_type = 'application/octet-stream'
            if resume.is_pdf:
                content_type = 'application/pdf'
            elif resume.is_docx:
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

            # Create response
            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{resume.original_filename}"'
            response['Content-Length'] = len(file_data)

            return response

        except Exception as e:
            raise Http404(f"File could not be served: {str(e)}")


class SetPrimaryResumeView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """Set a resume as primary."""
    model = Resume

    def post(self, request, *args, **kwargs):
        """Set resume as primary."""
        resume = self.get_object()

        # Set as primary (save method handles the logic)
        resume.is_primary = True
        resume.save()

        messages.success(
            request,
            f'"{resume.title}" is now your primary resume.'
        )
        return redirect('resumes:list')


class ResumePreviewView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """Preview parsed resume content."""
    model = Resume
    template_name = 'resumes/resume_preview.html'

    def get_context_data(self, **kwargs):
        """Add parsed data to context."""
        context = super().get_context_data(**kwargs)
        resume = self.object

        context['parsed_html'] = resume.parsed_text_html
        context['parsed_skills'] = resume.get_parsed_skills_list()
        context['parsed_education'] = resume.get_education_list()
        context['parsed_contact'] = resume.get_contact_info_dict()
        context['user_profile'] = _get_or_create_header_profile(self.request.user)

        return context


class ResumeReplaceFileView(LoginRequiredMixin, UserResumeMixin, UpdateView):
    """Replace resume file and re-parse."""
    model = Resume
    form_class = ResumeReplaceFileForm
    template_name = 'resumes/resume_replace.html'
    success_url = reverse_lazy('resumes:list')

    def form_valid(self, form):
        """Handle file replacement and trigger re-parsing."""
        resume = form.save()
        
        # Trigger re-parsing
        try:
            self._parse_resume(resume)
            messages.success(
                self.request,
                f'File replaced for "{resume.title}". Re-parsing in progress.'
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'File replaced but parsing failed: {str(e)}'
            )
        
        return super().form_valid(form)

    def _parse_resume(self, resume):
        """Parse resume (same as upload)."""
        resume.mark_as_parsing()

        try:
            result = resume_parser.parse_file(
                resume.file.path,
                resume.original_filename
            )

            if result.get('success'):
                resume.mark_as_parsed(result)
            else:
                error_msg = result.get('error', 'Unknown parsing error')
                resume.mark_as_failed(error_msg)

        except Exception as e:
            resume.mark_as_failed(str(e))
            raise


@login_required
@require_POST
def resume_reparse_view(request, pk):
    """Re-parse an existing resume."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)

    if not resume.can_reparse:
        messages.error(request, 'This resume cannot be re-parsed.')
        return redirect('resumes:detail', pk=pk)

    try:
        # Mark as parsing
        resume.mark_as_parsing()

        # Parse
        result = resume_parser.parse_file(
            resume.file.path,
            resume.original_filename
        )

        if result.get('success'):
            resume.mark_as_parsed(result)
            messages.success(request, f'Resume "{resume.title}" re-parsed successfully!')
        else:
            error_msg = result.get('error', 'Unknown parsing error')
            resume.mark_as_failed(error_msg)
            messages.error(request, f'Parsing failed: {error_msg}')

    except Exception as e:
        resume.mark_as_failed(str(e))
        messages.error(request, f'Re-parsing failed: {str(e)}')

    return redirect('resumes:detail', pk=pk)


@login_required
@require_POST
def resume_bulk_delete_view(request):
    """Bulk delete resumes."""
    form = BulkResumeDeleteForm(request.POST, user=request.user)
    
    if form.is_valid():
        resume_ids = form.cleaned_data['resume_ids']
        
        with transaction.atomic():
            deleted_count = Resume.objects.filter(
                user=request.user,
                pk__in=resume_ids
            ).delete()[0]
        
        messages.success(
            request,
            f'Successfully deleted {deleted_count} resume(s).'
        )
    else:
        messages.error(request, 'Invalid request.')
    
    return redirect('resumes:list')


@login_required
def resume_stats_api(request):
    """API endpoint for resume statistics."""
    resumes = Resume.objects.filter(user=request.user)
    
    stats = {
        'total': resumes.count(),
        'parsed': resumes.filter(status='parsed').count(),
        'parsing': resumes.filter(status='parsing').count(),
        'failed': resumes.filter(status='failed').count(),
        'uploaded': resumes.filter(status='uploaded').count(),
        'total_skills': sum(
            len(r.get_parsed_skills_list()) 
            for r in resumes.filter(status='parsed')
        ),
        'avg_experience': resumes.filter(
            experience_years__isnull=False
        ).values_list('experience_years', flat=True),
    }
    
    # Calculate average experience
    exp_values = list(stats['avg_experience'])
    stats['avg_experience'] = (
        sum(exp_values) / len(exp_values) if exp_values else 0
    )
    
    return JsonResponse(stats)


class ResumeComparisonView(LoginRequiredMixin, UserResumeMixin, TemplateView):
    """Compare multiple resumes for optimization insights."""
    template_name = 'resumes/resume_comparison.html'

    def get_context_data(self, **kwargs):
        """Add comparison data to context."""
        context = super().get_context_data(**kwargs)

        # Get resume IDs from query parameters
        resume_ids = self.request.GET.getlist('resumes')
        if resume_ids:
            try:
                resume_ids = [int(rid) for rid in resume_ids]
            except ValueError:
                resume_ids = []

        # Get all user's parsed resumes for selection
        user_resumes = self.get_queryset().filter(status='parsed').order_by('-uploaded_at')
        context['user_resumes'] = user_resumes

        # Perform comparison if resumes selected
        if resume_ids and len(resume_ids) >= 2:
            from .advanced_analysis import ResumeComparator
            comparator = ResumeComparator()
            comparison_result = comparator.compare_resumes(resume_ids, self.request.user.id)

            if comparison_result['success']:
                context['comparison'] = comparison_result
                context['selected_resumes'] = resume_ids

        return context


class IndustryBenchmarkView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """Benchmark resume against industry standards."""
    model = Resume
    template_name = 'resumes/resume_benchmark.html'
    context_object_name = 'resume'

    def get_context_data(self, **kwargs):
        """Add benchmark data to context."""
        context = super().get_context_data(**kwargs)
        resume = self.get_object()

        # Get industry from query params or default to general
        industry = self.request.GET.get('industry', 'general')

        # Perform optimization analysis
        from .optimization import ResumeOptimizer
        optimizer = ResumeOptimizer()
        analysis = optimizer.optimize_resume(resume.parsed_text or '')

        # Perform industry benchmarking
        from .advanced_analysis import IndustryBenchmarker
        benchmarker = IndustryBenchmarker()
        benchmark = benchmarker.benchmark_resume(analysis, industry)

        context['analysis'] = analysis
        context['benchmark'] = benchmark
        context['selected_industry'] = industry
        context['available_industries'] = [
            ('technology', 'Technology'),
            ('finance', 'Finance'),
            ('healthcare', 'Healthcare'),
            ('marketing', 'Marketing'),
            ('general', 'General')
        ]

        return context


class OptimizationHistoryView(LoginRequiredMixin, TemplateView):
    """View optimization history and progress tracking."""
    template_name = 'resumes/optimization_history.html'

    def get_context_data(self, **kwargs):
        """Add optimization history to context."""
        context = super().get_context_data(**kwargs)

        # Get time period from query params
        days = int(self.request.GET.get('days', 30))

        # Get optimization history
        from .advanced_analysis import OptimizationTracker
        tracker = OptimizationTracker()
        history = tracker.get_optimization_history(self.request.user.id, days)

        # Get user insights
        insights = tracker.get_user_insights(self.request.user.id)

        context['history'] = history
        context['insights'] = insights
        context['selected_days'] = days
        context['available_periods'] = [
            (7, 'Last 7 days'),
            (30, 'Last 30 days'),
            (90, 'Last 3 months'),
            (365, 'Last year')
        ]

        return context


@login_required
@require_POST
def compare_resumes(request):
    """AJAX endpoint for resume comparison."""
    try:
        resume_ids = request.POST.getlist('resume_ids[]')
        if not resume_ids or len(resume_ids) < 2:
            return JsonResponse({
                'success': False,
                'error': 'Please select at least 2 resumes to compare'
            })

        try:
            resume_ids = [int(rid) for rid in resume_ids]
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid resume IDs'
            })

        from .advanced_analysis import ResumeComparator
        comparator = ResumeComparator()
        result = comparator.compare_resumes(resume_ids, request.user.id)

        return JsonResponse({
            'success': result['success'],
            'data': result if result['success'] else None,
            'error': result.get('error') if not result['success'] else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def benchmark_resume(request, pk):
    """AJAX endpoint for industry benchmarking."""
    try:
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
        industry = request.GET.get('industry', 'general')

        # Perform analysis and benchmarking
        from .optimization import ResumeOptimizer
        from .advanced_analysis import IndustryBenchmarker

        optimizer = ResumeOptimizer()
        analysis = optimizer.optimize_resume(resume.parsed_text or '')

        benchmarker = IndustryBenchmarker()
        benchmark = benchmarker.benchmark_resume(analysis, industry)

        return JsonResponse({
            'success': True,
            'analysis': analysis,
            'benchmark': benchmark
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def advanced_optimize_resume(request, pk):
    """Advanced optimization with AI and personalization."""
    try:
        resume = get_object_or_404(Resume, pk=pk, user=request.user)

        if not resume.parsed_text:
            return JsonResponse({
                'success': False,
                'error': 'Resume must be parsed before optimization'
            })

        job_description = request.POST.get('job_description', '')

        # Get user history for personalization
        from .advanced_analysis import OptimizationTracker
        tracker = OptimizationTracker()
        user_history = tracker.get_user_insights(request.user.id)

        # Perform advanced optimization
        from .advanced_analysis import AdvancedResumeAdvisor
        advisor = AdvancedResumeAdvisor()
        result = advisor.generate_advanced_suggestions(
            resume.parsed_text,
            job_description,
            user_history
        )

        if result['success']:
            # Save advanced suggestions
            from .models import ResumeOptimization, ResumeSuggestion

            optimization, created = ResumeOptimization.objects.get_or_create(
                resume=resume,
                defaults={
                    'ats_score': 0,  # Will be calculated separately
                    'action_verb_score': 0,
                    'keyword_score': 0,
                    'overall_score': 0,
                    'suggestions': result['suggestions']
                }
            )

            if not created:
                optimization.suggestions = result['suggestions']
                optimization.save()

            # Create detailed suggestions
            ResumeSuggestion.objects.filter(optimization=optimization).delete()

            for suggestion_data in result['suggestions'][:8]:  # Limit to 8
                ResumeSuggestion.objects.create(
                    optimization=optimization,
                    category=suggestion_data.get('category', 'general'),
                    priority=suggestion_data.get('impact_level', 'medium'),
                    title=suggestion_data.get('title', 'Advanced Suggestion'),
                    description=suggestion_data.get('description', ''),
                    suggestion=suggestion_data.get('suggestion', ''),
                    example_before=suggestion_data.get('example_before', ''),
                    example_after=suggestion_data.get('example_after', '')
                )

        return JsonResponse({
            'success': result['success'],
            'suggestions': result.get('suggestions', []),
            'error': result.get('error') if not result['success'] else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


class ResumeOptimizationView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """Analyze and optimize a resume."""
    model = Resume
    template_name = 'resumes/resume_optimization.html'
    context_object_name = 'resume'

    def get_context_data(self, **kwargs):
        """Add optimization data to context."""
        context = super().get_context_data(**kwargs)
        resume = self.get_object()

        # Get job description from query params or session
        job_description = self.request.GET.get('job_description', '')

        # Perform optimization analysis
        from .optimization import ResumeOptimizer
        optimizer = ResumeOptimizer()
        optimization_results = optimizer.optimize_resume(
            resume.parsed_text or '',
            job_description if job_description else None
        )

        # Replace underscores with spaces in keyword category names
        if 'keywords' in optimization_results and 'keyword_counts' in optimization_results['keywords']:
            optimization_results['keywords']['keyword_counts'] = {
                k.replace('_', ' '): v 
                for k, v in optimization_results['keywords']['keyword_counts'].items()
            }

        # Replace underscores with spaces in ATS component names
        if 'ats' in optimization_results and 'component_scores' in optimization_results['ats']:
            optimization_results['ats']['component_scores'] = {
                k.replace('_', ' '): v 
                for k, v in optimization_results['ats']['component_scores'].items()
            }

        context['optimization'] = optimization_results
        context['job_description'] = job_description

        return context


class ResumeRewriteWorkspaceView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """Dedicated workspace for generating and editing AI rewrites."""
    model = Resume
    template_name = 'resumes/resume_rewrite_workspace.html'
    context_object_name = 'resume'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resume = self.object
        session_key = _get_rewrite_session_key(resume.pk)
        rewrite_preview = self.request.session.get(session_key)

        initial = {}
        if rewrite_preview:
            preview_context = rewrite_preview.get('context', {})
            initial.update({
                'job_title': preview_context.get('job_title', ''),
                'industry': preview_context.get('industry', ''),
                'highlights': preview_context.get('highlights', ''),
                'metrics_focus': preview_context.get('metrics_focus', ''),
                'job_description': preview_context.get('job_description', ''),
            })
        else:
            job_description = self.request.GET.get('job_description', '')
            if job_description:
                initial['job_description'] = job_description

        context['rewrite_form'] = ResumeRewriteForm(initial=initial)
        context['rewrite_preview'] = rewrite_preview
        context['rewrite_score_cards'] = _assemble_rewrite_score_cards(rewrite_preview)
        context['saved_rewrites'] = resume.rewrite_drafts.filter(status='saved')
        context['session_key'] = session_key
        return context


class ResumeSuggestionsView(LoginRequiredMixin, UserResumeMixin, DetailView):
    """List AI-generated suggestions derived from the latest optimization."""
    model = Resume
    template_name = 'resumes/resume_suggestions.html'
    context_object_name = 'resume'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        optimization = self.object.optimization
        if optimization:
            suggestions = list(optimization.detailed_suggestions.all())
            for suggestion in suggestions:
                suggestion.description_html = convert_markdown_to_html(suggestion.description)
                suggestion.suggestion_html = convert_markdown_to_html(suggestion.suggestion)
                suggestion.example_before_html = convert_markdown_to_html(suggestion.example_before)
                suggestion.example_after_html = convert_markdown_to_html(suggestion.example_after)
            context['suggestions'] = suggestions
        else:
            context['suggestions'] = []
        return context


class ResumeSuggestionDetailView(LoginRequiredMixin, TemplateView):
    """Detailed view for a single suggestion."""
    template_name = 'resumes/resume_suggestion_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resume = get_object_or_404(Resume, pk=self.kwargs['pk'], user=self.request.user)
        suggestion = get_object_or_404(
            ResumeSuggestion,
            pk=self.kwargs['suggestion_pk'],
            optimization__resume=resume
        )
        context['resume'] = resume
        context['suggestion'] = suggestion
        context['suggestion_html'] = {
            'description': convert_markdown_to_html(suggestion.description),
            'suggestion': convert_markdown_to_html(suggestion.suggestion),
            'example_before': convert_markdown_to_html(suggestion.example_before),
            'example_after': convert_markdown_to_html(suggestion.example_after),
        }
        return context


@login_required
@require_POST
def optimize_resume(request, pk):
    """AJAX endpoint to optimize a resume."""
    try:
        resume = get_object_or_404(Resume, pk=pk, user=request.user)

        if not resume.parsed_text:
            return JsonResponse({
                'success': False,
                'error': 'Resume must be parsed before optimization'
            })

        job_description = request.POST.get('job_description', '')

        # Perform optimization
        from .optimization import ResumeOptimizer
        optimizer = ResumeOptimizer()
        results = optimizer.optimize_resume(resume.parsed_text, job_description)

        # Save optimization results to database
        from .models import ResumeOptimization, ResumeSuggestion

        optimization, created = ResumeOptimization.objects.get_or_create(
            resume=resume,
            defaults={
                'ats_score': results['ats']['overall_score'],
                'action_verb_score': results['action_verbs']['score'],
                'keyword_score': results['keywords']['density_score'],
                'overall_score': results['overall_score'],
                'action_verb_analysis': results['action_verbs'],
                'keyword_analysis': results['keywords'],
                'suggestions': results['ai_suggestions']
            }
        )

        if not created:
            # Update existing optimization
            optimization.ats_score = results['ats']['overall_score']
            optimization.action_verb_score = results['action_verbs']['score']
            optimization.keyword_score = results['keywords']['density_score']
            optimization.overall_score = results['overall_score']
            optimization.action_verb_analysis = results['action_verbs']
            optimization.keyword_analysis = results['keywords']
            optimization.suggestions = results['ai_suggestions']
            optimization.save()

        # Create detailed suggestions
        ResumeSuggestion.objects.filter(optimization=optimization).delete()  # Clear old suggestions

        for suggestion_data in results['ai_suggestions'][:5]:  # Limit to 5
            ResumeSuggestion.objects.create(
                optimization=optimization,
                category=suggestion_data.get('category', 'general'),
                priority=suggestion_data.get('impact_level', 'medium'),
                title=suggestion_data.get('title', 'Improvement Suggestion'),
                description=suggestion_data.get('description', ''),
                suggestion=suggestion_data.get('suggestion', ''),
                example_before=suggestion_data.get('example_before', ''),
                example_after=suggestion_data.get('example_after', '')
            )

        return JsonResponse({
            'success': True,
            'results': results
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def resume_optimization_report(request, pk):
    """Generate PDF optimization report."""
    try:
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
        optimization = resume.optimization

        if not optimization:
            messages.error(request, 'No optimization data available. Please run optimization first.')
            return redirect('resumes:optimize', pk=pk)

        # For now, return JSON - could be enhanced to generate PDF
        report_data = {
            'resume_title': resume.title,
            'optimization_score': optimization.overall_score,
            'ats_score': optimization.ats_score,
            'action_verb_score': optimization.action_verb_score,
            'keyword_score': optimization.keyword_score,
            'suggestions': list(optimization.detailed_suggestions.values(
                'category', 'priority', 'title', 'description', 'suggestion'
            ))
        }

        return JsonResponse(report_data)

    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('resumes:detail', pk=pk)


def _get_rewrite_session_key(resume_pk):
    return f'rewrite_preview_{resume_pk}'


def _assemble_rewrite_score_cards(rewrite_preview):
    if not rewrite_preview:
        return []

    score_cards = rewrite_preview.get('score_cards', {})
    rewritten_scores = score_cards.get('rewritten', {})
    score_deltas = rewrite_preview.get('score_deltas', {})

    return [
        {
            'label': 'Overall',
            'score': rewritten_scores.get('overall_score'),
            'delta': score_deltas.get('overall_score', 0),
        },
        {
            'label': 'ATS',
            'score': rewritten_scores.get('ats_score'),
            'delta': score_deltas.get('ats_score', 0),
        },
        {
            'label': 'Action Verbs',
            'score': rewritten_scores.get('action_score'),
            'delta': score_deltas.get('action_score', 0),
        },
        {
            'label': 'Keywords',
            'score': rewritten_scores.get('keyword_score'),
            'delta': score_deltas.get('keyword_score', 0),
        },
    ]


def _get_rewrite_preview_from_session(request, pk, update_text=False):
    session_key = _get_rewrite_session_key(pk)
    preview = request.session.get(session_key)
    if not preview:
        return None

    if update_text:
        edited_text = request.POST.get('edited_text')
        if edited_text is not None:
            preview['rewritten_text'] = edited_text.strip()
            request.session[session_key] = preview
            request.session.modified = True

    return preview


def _get_original_score_card(resume, job_description=None):
    """Get baseline scores from the existing optimization cache or run analysis."""
    if resume.optimization:
        return {
            'overall_score': resume.optimization.overall_score,
            'ats_score': resume.optimization.ats_score,
            'action_score': resume.optimization.action_verb_score,
            'keyword_score': resume.optimization.keyword_score,
        }

    if not resume.parsed_text:
        return {
            'overall_score': 0,
            'ats_score': 0,
            'action_score': 0,
            'keyword_score': 0,
        }

    from .optimization import ResumeOptimizer

    optimizer = ResumeOptimizer()
    baseline = optimizer.optimize_resume(resume.parsed_text, job_description)

    return {
        'overall_score': baseline.get('overall_score', 0),
        'ats_score': baseline.get('ats', {}).get('overall_score', 0),
        'action_score': baseline.get('action_verbs', {}).get('score', 0),
        'keyword_score': baseline.get('keywords', {}).get('density_score', 0),
    }


def _build_score_deltas(original_scores, rewritten_scores):
    """Calculate how much each score changed in the rewrite."""
    deltas = {}
    for key, rewritten_value in rewritten_scores.items():
        original_value = original_scores.get(key, 0)
        deltas[key] = round((rewritten_value or 0) - (original_value or 0), 1)
    return deltas


def _parse_rewrite_text(rewritten_text: str, resume: Resume) -> dict:
    """Parse the rewritten text to capture structured data."""
    try:
        result = resume_parser.parse_content(
            rewritten_text.encode('utf-8', errors='ignore'),
            f"{resume.title[:40]}-rewrite.txt"
        )
        if result.get('success'):
            return result
    except Exception:
        pass
    return {}


def _create_resume_from_rewrite(original_resume: Resume, rewritten_text: str, parsed_data: dict, version_notes: str) -> Resume:
    """Persist a new Resume version that reflects the rewritten content."""
    new_resume = Resume(
        user=original_resume.user,
        title=original_resume.title,
        file=original_resume.file.name,
        original_filename=original_resume.original_filename,
        file_size=original_resume.file_size,
        status='parsed',
        parsed_text=rewritten_text,
        skills=parsed_data.get('skills', []),
        experience_years=parsed_data.get('experience_years'),
        education=parsed_data.get('education', []),
        contact_info=parsed_data.get('contact_info', {}),
        certifications=parsed_data.get('certifications', []),
        parsed_at=timezone.now(),
        version_notes=version_notes,
        is_primary=False,
    )
    new_resume.save()
    return new_resume


def _create_optimization_for_resume(resume_obj: Resume, optimization_data: dict):
    """Create optimization records for the newly created rewrite version."""
    action_data = optimization_data.get('action_verbs', {})
    keyword_data = optimization_data.get('keywords', {})
    ats_data = optimization_data.get('ats', {})

    optimization = ResumeOptimization.objects.create(
        resume=resume_obj,
        ats_score=ats_data.get('overall_score', 0),
        action_verb_score=action_data.get('score', 0),
        keyword_score=keyword_data.get('density_score', 0),
        overall_score=optimization_data.get('overall_score', 0),
        action_verb_analysis=action_data,
        keyword_analysis=keyword_data,
        suggestions=optimization_data.get('ai_suggestions', [])
    )

    ResumeSuggestion.objects.filter(optimization=optimization).delete()
    for suggestion_data in optimization_data.get('ai_suggestions', [])[:5]:
        ResumeSuggestion.objects.create(
            optimization=optimization,
            category=suggestion_data.get('category', 'general'),
            priority=suggestion_data.get('impact_level', 'medium'),
            title=suggestion_data.get('title', 'Rewrite Suggestion'),
            description=suggestion_data.get('description', ''),
            suggestion=suggestion_data.get('suggestion', ''),
            example_before=suggestion_data.get('example_before', ''),
            example_after=suggestion_data.get('example_after', '')
        )

    return optimization


@login_required
@require_POST
def load_saved_resume_rewrite(request, pk, draft_pk):
    """Load a previously saved rewrite preview back into the session."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    draft = get_object_or_404(
        ResumeRewriteDraft,
        pk=draft_pk,
        resume=resume,
        status='saved'
    )

    from .optimization import ResumeOptimizer

    optimizer = ResumeOptimizer()
    rewrite_optimization = optimizer.optimize_resume(
        draft.rewritten_text,
        job_description=draft.job_description
    )

    original_scores = _get_original_score_card(resume, job_description=draft.job_description)
    rewritten_scores = {
        'overall_score': rewrite_optimization.get('overall_score', 0),
        'ats_score': rewrite_optimization.get('ats', {}).get('overall_score', 0),
        'action_score': rewrite_optimization.get('action_verbs', {}).get('score', 0),
        'keyword_score': rewrite_optimization.get('keywords', {}).get('density_score', 0),
    }

    preview_payload = {
        'rewritten_text': draft.rewritten_text,
        'context': {
            'job_title': draft.job_title,
            'industry': draft.industry,
            'highlights': draft.highlights,
            'metrics_focus': draft.metrics_focus,
            'job_description': draft.job_description,
        },
        'optimization': rewrite_optimization,
        'score_cards': {
            'original': original_scores,
            'rewritten': rewritten_scores,
        },
        'score_deltas': _build_score_deltas(original_scores, rewritten_scores),
        'ai_raw_response': draft.optimization_snapshot.get('ai_suggestions', [])
    }

    session_key = _get_rewrite_session_key(pk)
    request.session[session_key] = preview_payload
    request.session.modified = True

    messages.success(request, 'Loaded saved rewrite into preview mode. Compare and save or discard.')
    return redirect('resumes:rewrite_workspace', pk=pk)


@login_required
@require_POST
def delete_saved_resume_rewrite(request, pk, draft_pk):
    """Permanently remove a saved rewrite draft."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    draft = get_object_or_404(
        ResumeRewriteDraft,
        pk=draft_pk,
        resume=resume,
        status='saved'
    )

    draft.delete()
    messages.info(request, 'Saved rewrite removed.')
    return redirect('resumes:rewrite_workspace', pk=pk)


@login_required
@require_POST
def resume_rewrite_preview(request, pk):
    """Generate an AI rewrite preview and stash it in the session."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    form = ResumeRewriteForm(request.POST or None)

    if not form.is_valid():
        messages.error(request, 'Please provide valid input to generate a rewrite.')
        return redirect('resumes:rewrite_workspace', pk=pk)

    if not resume.parsed_text:
        messages.error(request, 'Resume must be parsed before generating a rewrite.')
        return redirect('resumes:rewrite_workspace', pk=pk)

    rewriter = ResumeRewriter()
    ctx = {
        'job_title': form.cleaned_data.get('job_title', ''),
        'industry': form.cleaned_data.get('industry', ''),
        'highlights': form.cleaned_data.get('highlights', ''),
        'metrics_focus': form.cleaned_data.get('metrics_focus', ''),
        'job_description': form.cleaned_data.get('job_description', ''),
    }
    header_text = _build_header_text(request.user)

    rewrite_result = rewriter.rewrite_resume(
        resume.parsed_text,
        job_title=ctx['job_title'],
        industry=ctx['industry'],
        highlights=ctx['highlights'],
        metrics_focus=ctx['metrics_focus'],
        job_description=ctx['job_description'],
        header_text=header_text
    )

    if not rewrite_result.get('success'):
        messages.error(request, rewrite_result.get('error', 'Failed to rewrite resume.'))
        return redirect('resumes:rewrite_workspace', pk=pk)

    rewritten_text = (rewrite_result.get('rewritten_text') or '').strip()
    if not rewritten_text:
        messages.error(request, 'The AI rewrite did not return any content.')
        return redirect('resumes:rewrite_workspace', pk=pk)

    from .optimization import ResumeOptimizer

    optimizer = ResumeOptimizer()
    rewrite_optimization = optimizer.optimize_resume(
        rewritten_text,
        job_description=ctx['job_description']
    )

    original_scores = _get_original_score_card(resume, job_description=ctx['job_description'])
    rewritten_scores = {
        'overall_score': rewrite_optimization.get('overall_score', 0),
        'ats_score': rewrite_optimization.get('ats', {}).get('overall_score', 0),
        'action_score': rewrite_optimization.get('action_verbs', {}).get('score', 0),
        'keyword_score': rewrite_optimization.get('keywords', {}).get('density_score', 0),
    }

    preview_payload = {
        'rewritten_text': rewritten_text,
        'context': ctx,
        'optimization': rewrite_optimization,
        'score_cards': {
            'original': original_scores,
            'rewritten': rewritten_scores,
        },
        'score_deltas': _build_score_deltas(original_scores, rewritten_scores),
        'ai_raw_response': rewrite_result.get('raw_response', '')
    }

    session_key = _get_rewrite_session_key(pk)
    request.session[session_key] = preview_payload
    request.session.modified = True

    messages.success(request, 'AI rewrite generated—compare it below before saving or editing.')
    return redirect('resumes:rewrite_workspace', pk=pk)


@login_required
@require_POST
def save_resume_rewrite(request, pk):
    """Persist the rewrite preview as a draft."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    session_key = _get_rewrite_session_key(pk)
    preview = _get_rewrite_preview_from_session(request, pk, update_text=True)

    if not preview:
        messages.error(request, 'No rewrite preview found to save.')
        return redirect('resumes:rewrite_workspace', pk=pk)

    ResumeRewriteDraft.objects.create(
        resume=resume,
        rewritten_text=preview['rewritten_text'],
        job_title=preview['context'].get('job_title', ''),
        industry=preview['context'].get('industry', ''),
        highlights=preview['context'].get('highlights', ''),
        metrics_focus=preview['context'].get('metrics_focus', ''),
        job_description=preview['context'].get('job_description', ''),
        optimization_snapshot=preview['optimization'],
        status='saved'
    )

    request.session.pop(session_key, None)
    request.session.modified = True

    messages.success(request, 'Rewrite saved as a draft. You can revisit it from the rewrite workspace.')
    return redirect('resumes:rewrite_workspace', pk=pk)


@login_required
@require_POST
def discard_resume_rewrite(request, pk):
    """Forget the current rewrite preview."""
    session_key = _get_rewrite_session_key(pk)
    if session_key in request.session:
        request.session.pop(session_key)
        request.session.modified = True
        messages.info(request, 'Rewrite preview discarded.')
    else:
        messages.warning(request, 'No rewrite preview found to discard.')

    return redirect('resumes:rewrite_workspace', pk=pk)


@login_required
@require_POST
def apply_resume_rewrite(request, pk, draft_pk=None):
    """Persist the rewrite as a new resume version."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)

    if draft_pk:
        draft = get_object_or_404(
            ResumeRewriteDraft,
            pk=draft_pk,
            resume=resume,
            status='saved'
        )
        rewritten_text = draft.rewritten_text
        context = {
            'job_title': draft.job_title,
            'industry': draft.industry,
            'highlights': draft.highlights,
            'metrics_focus': draft.metrics_focus,
            'job_description': draft.job_description,
        }
        optimization_data = draft.optimization_snapshot or {}
        job_description = draft.job_description
    else:
        session_key = _get_rewrite_session_key(pk)
        preview = _get_rewrite_preview_from_session(request, pk, update_text=True)
        if not preview:
            messages.error(request, 'No rewrite preview available to apply.')
            return redirect('resumes:rewrite_workspace', pk=pk)
        rewritten_text = preview['rewritten_text']
        context = preview['context']
        optimization_data = preview['optimization'] or {}
        job_description = context.get('job_description', '')

    parsed_data = _parse_rewrite_text(rewritten_text, resume)
    version_notes = 'AI rewrite applied'
    if context.get('job_title'):
        version_notes += f" - {context['job_title']}"

    new_resume = _create_resume_from_rewrite(resume, rewritten_text, parsed_data, version_notes)
    _create_optimization_for_resume(new_resume, optimization_data)

    if not draft_pk:
        request.session.pop(session_key, None)
        request.session.modified = True

    messages.success(
        request,
        f'Rewrite applied as version {new_resume.version}. '
        'Find it in your resume list and continue iterating.'
    )
    return redirect('resumes:list')
