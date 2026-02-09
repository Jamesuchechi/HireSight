"""
Additional views for template system, AI rewrite, and export
Append these to apps/resumes/views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, FormView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from .models import Resume, ResumeTemplate, ResumeTemplateCustomization, AIRewriteSession
from .forms import AIRewriteWithTemplateForm
from .template_engine import ResumeTemplateRenderer
from .exporters import PDFResumeExporter, DOCXResumeExporter, PlainTextExporter
from .tasks import process_ai_rewrite_with_template


class TemplateGalleryView(LoginRequiredMixin, ListView):
    """Browse available resume templates"""
    model = ResumeTemplate
    template_name = 'resumes/template_gallery.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        """Get active templates, optionally filtered by category"""
        queryset = ResumeTemplate.objects.filter(is_active=True)
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-usage_count', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ResumeTemplate.CATEGORY_CHOICES
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class TemplatePreviewView(LoginRequiredMixin, DetailView):
    """Preview a specific template"""
    model = ResumeTemplate
    template_name = 'resumes/template_preview.html'
    context_object_name = 'template'
    
    def get_queryset(self):
        return ResumeTemplate.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's resumes for selection
        context['user_resumes'] = Resume.objects.filter(
            user=self.request.user,
            status='parsed'
        ).order_by('-uploaded_at')
        
        return context


class AIRewriteWithTemplateView(LoginRequiredMixin, FormView):
    """AI rewrite with template selection"""
    form_class = AIRewriteWithTemplateForm
    template_name = 'resumes/ai_rewrite_with_template.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.resume = get_object_or_404(
            Resume,
            pk=kwargs['pk'],
            user=request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resume'] = self.resume
        
        # Get available templates
        context['templates'] = ResumeTemplate.objects.filter(
            is_active=True
        ).order_by('category', 'name')
        
        # Get selected template if any
        template_id = self.request.GET.get('template')
        if template_id:
            try:
                context['selected_template'] = ResumeTemplate.objects.get(
                    pk=template_id,
                    is_active=True
                )
            except ResumeTemplate.DoesNotExist:
                pass
        
        return context
    
    def form_valid(self, form):
        """Process AI rewrite request"""
        template_id = form.cleaned_data.get('template_id')
        template = None
        
        if template_id:
            try:
                template = ResumeTemplate.objects.get(pk=template_id, is_active=True)
            except ResumeTemplate.DoesNotExist:
                pass
        
        # Create AI rewrite session
        session = AIRewriteSession.objects.create(
            resume=self.resume,
            template=template,
            llm_provider=form.cleaned_data['llm_provider'],
            job_title=form.cleaned_data.get('job_title', ''),
            industry=form.cleaned_data.get('industry', ''),
            highlights=form.cleaned_data.get('highlights', ''),
            metrics_focus=form.cleaned_data.get('metrics_focus', ''),
            job_description=form.cleaned_data.get('job_description', ''),
            additional_instructions=form.cleaned_data.get('additional_instructions', ''),
            original_content=self.resume.parsed_text or '',
            status='pending'
        )
        
        # Queue async processing
        process_ai_rewrite_with_template.delay(session.id)
        
        messages.success(
            self.request,
            f'AI rewrite started using {session.get_llm_provider_display()}. '
            'You will be notified when complete.'
        )
        
        return redirect('resumes:ai_rewrite_status', pk=self.resume.pk, session_id=session.id)
    
    def get_success_url(self):
        return self.request.path


class AIRewriteStatusView(LoginRequiredMixin, DetailView):
    """Check status of AI rewrite session"""
    model = AIRewriteSession
    template_name = 'resumes/ai_rewrite_status.html'
    context_object_name = 'session'
    pk_url_kwarg = 'session_id'
    
    def get_queryset(self):
        """Ensure user can only see their own sessions"""
        return AIRewriteSession.objects.filter(resume__user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resume'] = self.object.resume
        return context


@login_required
def ai_rewrite_status_api(request, session_id):
    """AJAX endpoint for checking rewrite status"""
    try:
        session = get_object_or_404(
            AIRewriteSession,
            pk=session_id,
            resume__user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'status': session.status,
            'rewritten_content': session.rewritten_content if session.status == 'completed' else None,
            'error_message': session.error_message if session.status == 'failed' else None,
            'tokens_used': session.tokens_used,
            'processing_time': session.processing_time_seconds,
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


class ExportResumeView(LoginRequiredMixin, DetailView):
    """Export resume in various formats"""
    model = Resume
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        resume = self.get_object()
        export_format = kwargs.get('format', 'pdf').lower()
        
        try:
            if export_format == 'pdf':
                return self._export_pdf(resume)
            elif export_format == 'docx':
                return self._export_docx(resume)
            elif export_format == 'txt':
                return self._export_txt(resume)
            else:
                messages.error(request, f'Unsupported export format: {export_format}')
                return redirect('resumes:detail', pk=resume.pk)
        
        except Exception as e:
            messages.error(request, f'Export failed: {str(e)}')
            return redirect('resumes:detail', pk=resume.pk)
    
    def _export_pdf(self, resume):
        """Export as PDF"""
        # Get template and customization
        try:
            customization = resume.template_customization
            template = customization.template
        except ResumeTemplateCustomization.DoesNotExist:
            # Use default template or create basic export
            template = ResumeTemplate.objects.filter(
                is_active=True,
                category='ats'
            ).first()
            customization = None
        
        if not template:
            # Fallback to plain text
            return self._export_txt(resume)
        
        # Render and export
        renderer = ResumeTemplateRenderer(template, customization)
        exporter = PDFResumeExporter(resume, renderer)
        pdf_buffer = exporter.export()
        
        # Create response
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{resume.title}.pdf"'
        
        return response
    
    def _export_docx(self, resume):
        """Export as DOCX"""
        try:
            customization = resume.template_customization
        except ResumeTemplateCustomization.DoesNotExist:
            customization = None
        
        exporter = DOCXResumeExporter(resume, customization)
        docx_buffer = exporter.export()
        
        # Create response
        response = HttpResponse(
            docx_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{resume.title}.docx"'
        
        return response
    
    def _export_txt(self, resume):
        """Export as plain text"""
        exporter = PlainTextExporter(resume)
        text_content = exporter.export()
        
        # Create response
        response = HttpResponse(text_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{resume.title}.txt"'
        
        return response
