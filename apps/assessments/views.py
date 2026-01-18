from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.views.generic.base import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Max, Q, Count, Avg, Prefetch
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.core.cache import cache
import logging

from .models import (
    SkillTest, SkillAssessmentAttempt, SkillBadge, 
    AssessmentCategory, QuestionPool
)
from .forms import TestFilterForm, QuestionGenerationForm
from .ai_utils import QuestionGenerator
from .utils import generate_certificate_pdf, get_client_ip

logger = logging.getLogger(__name__)


POOL_COUNT_CACHE_TIMEOUT = getattr(settings, 'QUESTION_POOL_COUNT_CACHE_TIMEOUT', 600)
GENERATION_COOLDOWN_SECONDS = getattr(settings, 'ASSESSMENT_GENERATION_COOLDOWN_SECONDS', 300)

def _question_types_key(question_types):
    if not question_types:
        return 'any'
    return '-'.join(sorted(question_types))

def get_pool_count_cache_key(skill_name, difficulty, question_types):
    types_key = _question_types_key(question_types)
    return f"assessments:pool_count:{skill_name.lower()}:{difficulty}:{types_key}"

def get_cached_question_pool_count(skill_name, difficulty, question_types):
    cache_key = get_pool_count_cache_key(skill_name, difficulty, question_types)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    count = QuestionPool.objects.filter(
        skill_name__iexact=skill_name,
        difficulty=difficulty,
        question_type__in=question_types,
        is_active=True
    ).count()
    cache.set(cache_key, count, POOL_COUNT_CACHE_TIMEOUT)
    return count

def refresh_question_pool_cache(skill_name, difficulty, question_types):
    cache_key = get_pool_count_cache_key(skill_name, difficulty, question_types)
    cache.delete(cache_key)
    return get_cached_question_pool_count(skill_name, difficulty, question_types)

def get_generation_cooldown_key(slug):
    return f"assessments:generate_cooldown:{slug}"

def get_generation_cooldown_remaining(slug):
    timestamp = cache.get(get_generation_cooldown_key(slug))
    if not timestamp:
        return 0
    elapsed = timezone.now().timestamp() - float(timestamp)
    remaining = GENERATION_COOLDOWN_SECONDS - elapsed
    return int(remaining) if remaining > 0 else 0


class PersonalAccountRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only personal accounts can access"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.account_type == 'personal'
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only job seekers can access skill assessments.')
        return redirect('dashboard:dashboard_home')


class BrowseTestsView(LoginRequiredMixin, PersonalAccountRequiredMixin, ListView):
    """Browse available skill tests with filtering and recommendations"""
    
    model = SkillTest
    template_name = 'assessments/browse.html'
    context_object_name = 'tests'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = SkillTest.objects.filter(is_active=True).select_related()
        
        # Get user's skills for matching
        user_skills = []
        if hasattr(self.request.user, 'personal_profile'):
            user_skills = [s.get('skill', '').lower() for s in self.request.user.personal_profile.skills]
        
        # Apply filters
        form = TestFilterForm(self.request.GET)
        if form.is_valid():
            skill_filter = form.cleaned_data.get('skill', '').strip()
            difficulty_filter = form.cleaned_data.get('difficulty', '')
            test_type_filter = form.cleaned_data.get('test_type', '')
            sort_by = form.cleaned_data.get('sort_by', '')
            
            if skill_filter:
                queryset = queryset.filter(
                    Q(skill_name__icontains=skill_filter) |
                    Q(title__icontains=skill_filter) |
                    Q(description__icontains=skill_filter)
                )
            
            if difficulty_filter:
                queryset = queryset.filter(difficulty=difficulty_filter)
            
            if test_type_filter:
                queryset = queryset.filter(test_type=test_type_filter)
            
            # Sorting
            if sort_by == 'popular':
                queryset = queryset.order_by('-total_attempts', '-average_score')
            elif sort_by == 'difficulty':
                queryset = queryset.order_by('difficulty', 'skill_name')
            elif sort_by == 'newest':
                queryset = queryset.order_by('-created_at')
            elif sort_by == 'oldest':
                queryset = queryset.order_by('created_at')
            elif sort_by == 'recommended':
                # Prioritize tests matching user skills
                if user_skills:
                    queryset = sorted(queryset, key=lambda t: (
                        t.skill_name.lower() in user_skills,
                        -t.total_attempts
                    ), reverse=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's best scores
        completed = SkillAssessmentAttempt.objects.filter(
            user=self.request.user,
            status='COMPLETED'
        ).values('test_id').annotate(best=Max('score'))
        best_scores = {str(item['test_id']): item['best'] for item in completed}
        
        # Get user's badges
        user_badges = set(SkillBadge.objects.filter(
            user=self.request.user
        ).values_list('test_id', flat=True))
        
        # Prepare test data with user's best score and badge status
        tests_data = []
        for test in context['tests']:
            filters = test.question_pool_filters or {}
            difficulty = filters.get('difficulty', test.difficulty)
            question_types = filters.get('types', ['MULTIPLE_CHOICE', 'TRUE_FALSE'])
            pool_count = get_cached_question_pool_count(test.skill_name, difficulty, question_types)
            cooldown_remaining = get_generation_cooldown_remaining(test.slug)
            tests_data.append({
                'test': test,
                'best_score': best_scores.get(str(test.id)),
                'has_badge': test.id in user_badges,
                'matches_skills': test.matches_user_skills(self.request.user),
                'pool_count': pool_count,
                'cooldown_remaining': cooldown_remaining
            })
        
        context['tests_data'] = tests_data
        context['form'] = TestFilterForm(self.request.GET)
        context['categories'] = AssessmentCategory.objects.filter(is_active=True).prefetch_related('tests')
        context['total_tests'] = SkillTest.objects.filter(is_active=True).count()
        context['user_badges_count'] = SkillBadge.objects.filter(user=self.request.user).count()
        
        # Get available skills for filter
        context['skills'] = SkillTest.objects.filter(
            is_active=True
        ).values_list('skill_name', flat=True).distinct().order_by('skill_name')
        
        return context


class GenerateQuestionsPageView(LoginRequiredMixin, PersonalAccountRequiredMixin, FormView):
    """Page where a user can request AI-generated questions for any skill"""

    template_name = 'assessments/generate_questions.html'
    form_class = QuestionGenerationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Generate AI Questions'
        return context

    def form_valid(self, form):
        skill_name = form.cleaned_data['skill_name']
        difficulty = form.cleaned_data['difficulty']
        question_type = form.cleaned_data['question_type']
        question_count = form.cleaned_data['question_count']

        try:
            generator = QuestionGenerator()
        except (ValueError, ImportError) as exc:
            messages.error(self.request, f"Question generation unavailable: {str(exc)}")
            return redirect('assessments:browse')

        generated = generator.generate_questions(
            skill_name=skill_name,
            difficulty=difficulty,
            count=question_count,
            question_type=question_type
        )

        if not generated:
            messages.warning(self.request, 'No questions were generated. Please try again.')
            return redirect('assessments:browse')

        created_count = 0
        for q_data in generated:
            question, created = QuestionPool.objects.get_or_create(
                skill_name=skill_name,
                difficulty=difficulty,
                question_type=question_type,
                question=q_data['question'],
                defaults={
                    'options': q_data.get('options', []),
                    'correct_answer': q_data.get('correct_answer'),
                    'explanation': q_data.get('explanation', ''),
                    'points': q_data.get('points', 10),
                    'estimated_time_seconds': q_data.get('estimated_time_seconds', 60),
                    'is_verified': False
                }
            )
            if created:
                created_count += 1

        if created_count == 0:
            messages.warning(
                self.request,
                f"AI generated {len(generated)} question(s) but none were new; they likely already exist in the question pool."
            )
            return redirect('assessments:browse')

        # Refresh cache so browse page shows newly created questions immediately
        cache_question_types = [question_type]
        refresh_question_pool_cache(skill_name, difficulty, cache_question_types)
        default_cache_types = ['MULTIPLE_CHOICE', 'TRUE_FALSE']
        if set(default_cache_types) != set(cache_question_types):
            refresh_question_pool_cache(skill_name, difficulty, default_cache_types)

        # Ensure a dynamic SkillTest exists so the new skill shows up on Browse
        existing_test = SkillTest.objects.filter(
            skill_name__iexact=skill_name,
            difficulty=difficulty,
            test_type='DYNAMIC',
            is_active=True
        ).first()

        if not existing_test:
            title = f"{skill_name} Practice Test"
            description = f"AI-generated practice questions for {skill_name} at {difficulty.title()} level."
            question_pool_filters = {'difficulty': difficulty, 'types': [question_type]}
            duration_minutes = max(20, question_count * 2)
            SkillTest.objects.create(
                title=title,
                skill_name=skill_name,
                description=description,
                test_type='DYNAMIC',
                difficulty=difficulty,
                duration_minutes=duration_minutes,
                passing_score=70,
                question_count=question_count,
                question_pool_filters=question_pool_filters,
                required_skills=[skill_name],
                is_active=True,
                is_featured=False
            )
        else:
            filters = existing_test.question_pool_filters or {}
            types = set(filters.get('types', []))
            types.add(question_type)
            filters['types'] = list(types)
            filters.setdefault('difficulty', difficulty)
            updated_fields = []
            if existing_test.question_pool_filters != filters:
                existing_test.question_pool_filters = filters
                updated_fields.append('question_pool_filters')
            if existing_test.question_count < question_count:
                existing_test.question_count = question_count
                updated_fields.append('question_count')
            if updated_fields:
                existing_test.save(update_fields=updated_fields)

        messages.success(
            self.request,
            f"Successfully generated {len(generated)} questions for {skill_name} ({created_count} new entries saved)."
        )
        return redirect('assessments:browse')


class TestDetailView(LoginRequiredMixin, PersonalAccountRequiredMixin, DetailView):
    """View test details before starting"""
    
    model = SkillTest
    template_name = 'assessments/test_detail.html'
    context_object_name = 'test'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's previous attempts
        context['previous_attempts'] = SkillAssessmentAttempt.objects.filter(
            user=self.request.user,
            test=self.object,
            status='COMPLETED'
        ).order_by('-completed_at')[:5]
        
        # Get user's best score
        best = SkillAssessmentAttempt.objects.filter(
            user=self.request.user,
            test=self.object,
            status='COMPLETED'
        ).aggregate(best=Max('score'))
        context['best_score'] = best['best']
        
        # Check if user has badge
        context['has_badge'] = SkillBadge.objects.filter(
            user=self.request.user,
            test=self.object
        ).exists()
        
        # Check if user has in-progress attempt
        context['in_progress_attempt'] = SkillAssessmentAttempt.objects.filter(
            user=self.request.user,
            test=self.object,
            status='IN_PROGRESS'
        ).first()
        
        return context


class StartTestView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    """Start a new assessment attempt"""
    
    def post(self, request, test_id):
        test = get_object_or_404(SkillTest, id=test_id, is_active=True)
        
        # Check for existing in-progress attempt
        existing_attempt = SkillAssessmentAttempt.objects.filter(
            user=request.user,
            test=test,
            status='IN_PROGRESS'
        ).first()
        
        if existing_attempt:
            # Check if time expired
            if existing_attempt.is_time_expired():
                existing_attempt.status = 'EXPIRED'
                existing_attempt.save()
                messages.warning(request, 'Your previous attempt expired. Starting a new one.')
            else:
                messages.info(request, 'Resuming your previous attempt.')
                return redirect('assessments:take', attempt_id=existing_attempt.id)
        
        # Create new attempt
        try:
            with transaction.atomic():
                # Generate questions for this attempt
                frozen_questions = test.generate_questions()
                
                if not frozen_questions:
                    messages.error(request, 'No questions available for this test. Please try another test.')
                    return redirect('assessments:browse')
                
                attempt = SkillAssessmentAttempt.objects.create(
                    user=request.user,
                    test=test,
                    frozen_questions=frozen_questions,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
            
            logger.info(f"User {request.user.email} started assessment {test.title} (attempt {attempt.id})")
            messages.success(request, f'Assessment started! You have {test.duration_minutes} minutes.')
            return redirect('assessments:take', attempt_id=attempt.id)
        
        except Exception as e:
            logger.error(f"Error starting assessment: {str(e)}")
            messages.error(request, 'Unable to start assessment. Please try again.')
            return redirect('assessments:test_detail', slug=test.slug)


class TakeTestView(LoginRequiredMixin, PersonalAccountRequiredMixin, DetailView):
    """Take the assessment with real-time timer and auto-save"""
    
    model = SkillAssessmentAttempt
    template_name = 'assessments/take_test.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_id'
    
    def get_queryset(self):
        return SkillAssessmentAttempt.objects.filter(user=self.request.user).select_related('test')
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Check if already completed
        if self.object.status != 'IN_PROGRESS':
            messages.info(request, 'This assessment has already been completed.')
            return redirect('assessments:results', attempt_id=self.object.id)
        
        # Check time limit
        if self.object.is_time_expired():
            self.object.status = 'EXPIRED'
            self.object.time_limit_exceeded = True
            self.object.save()
            messages.error(request, 'Time limit exceeded. Assessment automatically submitted.')
            return redirect('assessments:results', attempt_id=self.object.id)
        
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if self.object.status != 'IN_PROGRESS':
            messages.error(request, 'This assessment cannot be modified.')
            return redirect('assessments:results', attempt_id=self.object.id)
        
        try:
            with transaction.atomic():
                # Save all answers
                answers = {}
                for key, value in request.POST.items():
                    if key.startswith('question_'):
                        question_id = key.replace('question_', '')
                        answers[question_id] = value
                
                # Mark as completed
                self.object.answers = answers
                self.object.status = 'COMPLETED'
                self.object.completed_at = timezone.now()
                self.object.time_taken_minutes = self.object.get_elapsed_time()
                self.object.save()
                
                # Calculate score
                self.object.calculate_score()
                
                # Award badge if passed
                if self.object.passed:
                    badge, created = SkillBadge.objects.get_or_create(
                        user=request.user,
                        test=self.object.test,
                        defaults={'attempt': self.object}
                    )
                    if created:
                        logger.info(f"Badge awarded to {request.user.email} for {self.object.test.title}")
                        messages.success(request, f'🎉 Congratulations! You earned the {badge.badge_name} badge!')
            
            messages.success(request, 'Assessment submitted successfully!')
            logger.info(
                f"User {request.user.email} completed assessment {self.object.test.title} "
                f"with {self.object.score}% (passed={self.object.passed})"
            )
            return redirect('assessments:results', attempt_id=self.object.id)
        
        except Exception as e:
            logger.error(
                f"Error submitting assessment for {request.user.email} "
                f"on {self.object.test.title if self.object else 'unknown'}: {str(e)}"
            )
            messages.error(request, 'Error submitting assessment. Please try again.')
            return redirect('assessments:take', attempt_id=self.object.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        elapsed = self.object.get_elapsed_time()
        context['time_remaining'] = max(0, self.object.test.duration_minutes - elapsed)
        context['total_questions'] = len(self.object.frozen_questions)
        context['answered_questions'] = len([k for k in self.object.answers.keys() if self.object.answers[k]])
        context['progress_percentage'] = int((context['answered_questions'] / context['total_questions']) * 100) if context['total_questions'] > 0 else 0
        
        return context


class GenerateQuestionsView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    """Personal-user endpoint to bulk generate questions for a test"""

    def post(self, request, slug):
        test = get_object_or_404(SkillTest, slug=slug, is_active=True)
        filters = test.question_pool_filters or {}
        difficulty = filters.get('difficulty', test.difficulty)
        question_types = filters.get('types', ['MULTIPLE_CHOICE', 'TRUE_FALSE'])
        cooldown_remaining = get_generation_cooldown_remaining(test.slug)
        cooldown_key = get_generation_cooldown_key(test.slug)

        if cooldown_remaining:
            return JsonResponse({
                'success': False,
                'error': f'Please wait {cooldown_remaining}s before generating again.',
                'cooldown': cooldown_remaining
            }, status=429)
        
        try:
            generator = QuestionGenerator()
        except (ValueError, ImportError) as exc:
            logger.warning(f"Question generation skipped for {test.title}: {exc}")
            return JsonResponse({'success': False, 'error': str(exc)}, status=400)

        try:
            created_count = generator.bulk_generate_for_test(test)
            if created_count:
                message = f"Generated {created_count} new questions for {test.title}."
                cooldown_seconds = GENERATION_COOLDOWN_SECONDS
            else:
                message = f"No new questions were generated for {test.title}."
                cooldown_seconds = 0
            logger.info(f"{request.user.email} triggered question generation for {test.title}")
            if cooldown_seconds:
                cache.set(cooldown_key, timezone.now().timestamp(), cooldown_seconds)
            latest_pool_count = refresh_question_pool_cache(test.skill_name, difficulty, question_types)
            return JsonResponse({
                'success': True,
                'created_count': created_count,
                'message': message,
                'cooldown': cooldown_seconds,
                'pool_count': latest_pool_count
            })
        except Exception as exc:
            logger.error(f"Error generating questions for {test.title}: {exc}")
            return JsonResponse(
                {'success': False, 'error': 'Failed to generate questions. Check logs for details.'},
                status=500
            )


class SaveProgressView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    """AJAX endpoint to auto-save progress"""
    
    def post(self, request, attempt_id):
        try:
            attempt = get_object_or_404(
                SkillAssessmentAttempt,
                id=attempt_id,
                user=request.user,
                status='IN_PROGRESS'
            )
            
            question_id = request.POST.get('question_id')
            answer = request.POST.get('answer')
            
            if question_id and answer is not None:
                attempt.answers[question_id] = answer
                attempt.save(update_fields=['answers'])
                
                answered_count = len([k for k in attempt.answers.keys() if attempt.answers[k]])
                
                return JsonResponse({
                    'success': True,
                    'message': 'Progress saved',
                    'answered_count': answered_count,
                    'total_questions': len(attempt.frozen_questions)
                })
            
            return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
        
        except Exception as e:
            logger.error(f"Error saving progress: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class ViewResultsView(LoginRequiredMixin, PersonalAccountRequiredMixin, DetailView):
    """View assessment results with detailed breakdown"""
    
    model = SkillAssessmentAttempt
    template_name = 'assessments/results.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_id'
    
    def get_queryset(self):
        return SkillAssessmentAttempt.objects.filter(user=self.request.user).select_related('test')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.object.status != 'COMPLETED':
            messages.warning(self.request, 'Assessment not completed yet.')
        
        # Get badge if earned
        if self.object.passed:
            context['badge'] = SkillBadge.objects.filter(
                user=self.request.user,
                test=self.object.test
            ).first()
        
        # Calculate performance metrics
        if self.object.question_results:
            correct_count = sum(1 for r in self.object.question_results.values() if r.get('correct'))
            context['correct_count'] = correct_count
            context['incorrect_count'] = len(self.object.question_results) - correct_count
        
        # Get percentile ranking
        all_scores = SkillAssessmentAttempt.objects.filter(
            test=self.object.test,
            status='COMPLETED'
        ).values_list('score', flat=True)
        
        if all_scores and self.object.score is not None:
            scores_below = sum(1 for s in all_scores if s < self.object.score)
            context['percentile'] = int((scores_below / len(all_scores)) * 100)
        
        return context


class DownloadCertificateView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    """Generate and download PDF certificate"""
    
    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            SkillAssessmentAttempt.select_related('test'),
            id=attempt_id,
            user=request.user
        )
        
        if attempt.status != 'COMPLETED' or not attempt.passed:
            messages.error(request, 'Certificate not available for this assessment.')
            return redirect('assessments:results', attempt_id=attempt_id)
        
        try:
            # Get badge
            badge = SkillBadge.objects.filter(
                user=request.user,
                test=attempt.test
            ).first()
            
            if not badge:
                messages.error(request, 'Badge not found.')
                return redirect('assessments:results', attempt_id=attempt_id)
            
            pdf_content = generate_certificate_pdf(badge)
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="certificate_{attempt.test.skill_name}_{attempt.id}.pdf"'
            logger.info(f"Certificate downloaded by {request.user.email} for {attempt.test.title}")
            return response

        except Exception as e:
            logger.error(f"Error generating certificate PDF: {str(e)}")
            messages.error(request, 'Error generating certificate. Please try again later.')
            return redirect('assessments:results', attempt_id=attempt_id)


class MyBadgesView(LoginRequiredMixin, PersonalAccountRequiredMixin, ListView):
    """Display user's earned badges"""
    
    model = SkillBadge
    template_name = 'assessments/my_badges.html'
    context_object_name = 'badges'
    paginate_by = 12
    
    def get_queryset(self):
        return SkillBadge.objects.filter(
            user=self.request.user
        ).select_related('test', 'attempt').order_by('-issued_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get badge statistics
        badges = self.get_queryset()
        context['total_badges'] = badges.count()
        
        if badges:
            # Group by difficulty
            difficulty_counts = {}
            for badge in badges:
                diff = badge.badge_level
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            context['difficulty_counts'] = difficulty_counts
            
            # Group by skill
            skill_counts = {}
            for badge in badges:
                skill = badge.test.skill_name
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
            context['skill_counts'] = skill_counts
        
        return context


class VerifyBadgeView(DetailView):
    """Public badge verification page"""
    
    model = SkillBadge
    template_name = 'assessments/badge_detail.html'
    context_object_name = 'badge'
    slug_field = 'verification_code'
    slug_url_kwarg = 'verification_code'
    
    def get_queryset(self):
        return SkillBadge.objects.select_related('user', 'test', 'attempt')
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Increment view count
        self.object.view_count += 1
        self.object.save(update_fields=['view_count'])
        
        # Check if expired
        if self.object.is_expired():
            messages.warning(request, 'This badge has expired.')
        
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
