from datetime import timedelta
import json
import logging
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.core.mail import mail_admins
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Max, Prefetch, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, UpdateView
from django.views.generic.base import View
from django_ratelimit.decorators import ratelimit

from .analytics import AssessmentAnalytics
from .ai_utils import QuestionGenerator
from .forms import TestFilterForm, QuestionGenerationForm, GroupChallengeForm, DiscussionForm
from .models import (
    Achievement, BookmarkedQuestion, GroupChallenge, QuestionDiscussion,
    QuestionPool, SkillAssessmentAttempt, SkillBadge,
    SkillTest, StudyGroup, StudyGroupMembership, UserAchievement,
    AssessmentCategory
)
from .utils import LearningPathGenerator, generate_certificate_pdf, generate_results_pdf, get_client_ip

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


def render_rate_limit(request, rate_label):
    retry = getattr(request, 'limited_until', None)
    wait_message = 'later'
    if retry:
        delta = retry - timezone.now()
        if delta.total_seconds() > 0:
            minutes = int(delta.total_seconds() // 60)
            seconds = int(delta.total_seconds() % 60)
            wait_message = f"in {minutes}m {seconds}s" if minutes else f"in {seconds}s"
    messages.warning(
        request,
        f"Rate limit exceeded ({rate_label}). Please try again {wait_message}."
    )
    return render(
        request,
        'assessments/rate_limited.html',
        {'rate': rate_label, 'wait_message': wait_message},
        status=429
    )

def get_generation_cooldown_key(slug):
    return f"assessments:generate_cooldown:{slug}"

def get_generation_cooldown_remaining(slug):
    timestamp = cache.get(get_generation_cooldown_key(slug))
    if not timestamp:
        return 0
    elapsed = timezone.now().timestamp() - float(timestamp)
    remaining = GENERATION_COOLDOWN_SECONDS - elapsed
    return int(remaining) if remaining > 0 else 0


def get_or_create_custom_practice_test():
    defaults = {
        'title': 'Bookmarked Practice Session',
        'skill_name': 'Custom Practice',
        'description': 'Practice questions you bookmarked for focused review.',
        'test_type': 'STATIC',
        'difficulty': 'BEGINNER',
        'duration_minutes': 45,
        'passing_score': 0,
        'question_count': 0,
        'required_skills': [],
        'is_active': True
    }
    test, created = SkillTest.objects.get_or_create(slug='bookmarked-practice', defaults=defaults)
    if created:
        test.questions = []
        test.save(update_fields=['questions'])
    return test


def can_retake_today(user, test):
    today = timezone.localdate()
    return SkillAssessmentAttempt.objects.filter(
        user=user,
        test=test,
        started_at__date=today,
        is_practice_mode=False
    ).count() < (test.max_retakes_per_day or 0)


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


@method_decorator(ratelimit(key='ip', rate='20/h', method='POST', block=False), name='dispatch')
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
        
        if getattr(request, 'limited', False):
            return render_rate_limit(request, '20 test starts per hour')

        if existing_attempt:
            # Check if time expired
            if existing_attempt.is_time_expired():
                existing_attempt.status = 'EXPIRED'
                existing_attempt.save()
                messages.warning(request, 'Your previous attempt expired. Starting a new one.')
            else:
                messages.info(request, 'Resuming your previous attempt.')
                return redirect('assessments:take', attempt_id=existing_attempt.id)
        
        practice_param = request.POST.get('practice') or request.GET.get('practice', 'false')
        practice_mode = str(practice_param).strip().lower() in ('1', 'true', 'yes')
        if not practice_mode and not can_retake_today(request.user, test):
            reset_time = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            messages.error(
                request,
                f"You reached the daily retake limit (max {test.max_retakes_per_day}) for this test. "
                f"Try again after {reset_time.strftime('%I:%M %p')}."
            )
            return redirect('assessments:test_detail', slug=test.slug)
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
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    is_practice_mode=practice_mode
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
                
                # Award badge if passed (skip in practice mode)
                if self.object.passed and not self.object.is_practice_mode:
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
        context['practice_mode'] = self.object.is_practice_mode
        context['questions'] = self._prepare_questions_for_display()
        
        return context

    def _prepare_questions_for_display(self):
        questions = []
        for question in self.object.frozen_questions:
            q = question.copy()
            q['display_answer_text'] = self._get_answer_text(question)
            questions.append(q)
        return questions

    def _get_answer_text(self, question):
        answer_value = question.get('correct_answer')
        options = question.get('options') or []

        try:
            index = int(answer_value)
        except (TypeError, ValueError):
            index = None

        if index is not None and 0 <= index < len(options):
            return options[index]

        return answer_value


@method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=False), name='dispatch')
class GenerateQuestionsView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    """Personal-user endpoint to bulk generate questions for a test"""

    def post(self, request, slug):
        test = get_object_or_404(SkillTest, slug=slug, is_active=True)
        filters = test.question_pool_filters or {}
        difficulty = filters.get('difficulty', test.difficulty)
        question_types = filters.get('types', ['MULTIPLE_CHOICE', 'TRUE_FALSE'])
        cooldown_remaining = get_generation_cooldown_remaining(test.slug)
        cooldown_key = get_generation_cooldown_key(test.slug)

        if getattr(request, 'limited', False):
            return render_rate_limit(request, '10 question generations per hour')

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

        question_entries = []
        results_map = self.object.question_results or {}
        for idx, question in enumerate(self.object.frozen_questions, start=1):
            result = results_map.get(str(question.get('id')), {})
            question_entries.append({
                'question': question,
                'result': result,
                'number': idx
            })

        paginator = Paginator(question_entries, 10)
        page_number = self.request.GET.get('page') or 1
        questions_page = paginator.get_page(page_number)

        page_jump_options = []
        per_page = paginator.per_page
        for page_num in paginator.page_range:
            start = (page_num - 1) * per_page + 1
            page_jump_options.append({
                'page': page_num,
                'label': f"Question {start}"
            })

        context.update({
            'questions_page': questions_page,
            'page_obj': questions_page,
            'paginator': paginator,
            'questions_count': paginator.count,
            'page_jump_options': page_jump_options
        })
        
        return context


class ExportResultsPDFView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    """Export assessment attempt details as a PDF."""

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            SkillAssessmentAttempt,
            id=attempt_id,
            user=request.user,
            status='COMPLETED'
        )
        pdf_content = generate_results_pdf(attempt)
        filename = f"assessment_{attempt.test.slug}_{attempt.id}.pdf"
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


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
    



class AssessmentHistoryView(LoginRequiredMixin, PersonalAccountRequiredMixin, TemplateView):
    """Comprehensive assessment history with analytics"""
    
    template_name = 'assessments/history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all completed attempts
        all_attempts = SkillAssessmentAttempt.objects.filter(
            user=user,
            status='COMPLETED'
        ).select_related('test').order_by('-completed_at')
        
        # Separate passed and failed
        passed_attempts = all_attempts.filter(passed=True)
        failed_attempts = all_attempts.filter(passed=False)
        
        # Group by skill for analytics
        skill_stats = defaultdict(lambda: {
            'total': 0, 'passed': 0, 'failed': 0, 
            'best_score': 0, 'avg_score': 0, 'total_time': 0,
            'attempts': []
        })
        
        for attempt in all_attempts:
            skill = attempt.test.skill_name
            skill_stats[skill]['total'] += 1
            skill_stats[skill]['attempts'].append(attempt)
            skill_stats[skill]['total_time'] += attempt.time_taken_minutes or 0
            
            if attempt.passed:
                skill_stats[skill]['passed'] += 1
            else:
                skill_stats[skill]['failed'] += 1
            
            if attempt.score and attempt.score > skill_stats[skill]['best_score']:
                skill_stats[skill]['best_score'] = attempt.score
        
        # Calculate averages
        for skill, stats in skill_stats.items():
            scores = [a.score for a in stats['attempts'] if a.score]
            stats['avg_score'] = round(sum(scores) / len(scores), 1) if scores else 0
            stats['avg_time'] = round(stats['total_time'] / stats['total'], 1) if stats['total'] > 0 else 0
            stats['pass_rate'] = round((stats['passed'] / stats['total']) * 100, 1) if stats['total'] > 0 else 0
        
        # Overall statistics
        total_attempts = all_attempts.count()
        total_passed = passed_attempts.count()
        total_time_spent = sum(a.time_taken_minutes or 0 for a in all_attempts)
        
        # Time series data for chart (last 30 days)
        from datetime import timedelta
        from django.utils import timezone
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_attempts = all_attempts.filter(completed_at__gte=thirty_days_ago)
        
        # Group by date
        daily_data = defaultdict(lambda: {'passed': 0, 'failed': 0, 'scores': []})
        for attempt in recent_attempts:
            date_key = attempt.completed_at.strftime('%Y-%m-%d')
            if attempt.passed:
                daily_data[date_key]['passed'] += 1
            else:
                daily_data[date_key]['failed'] += 1
            if attempt.score:
                daily_data[date_key]['scores'].append(attempt.score)
        
        # Prepare chart data
        chart_labels = []
        chart_passed = []
        chart_failed = []
        chart_avg_scores = []
        
        for i in range(30):
            date = timezone.now() - timedelta(days=29-i)
            date_key = date.strftime('%Y-%m-%d')
            chart_labels.append(date.strftime('%b %d'))
            
            day_data = daily_data.get(date_key, {'passed': 0, 'failed': 0, 'scores': []})
            chart_passed.append(day_data['passed'])
            chart_failed.append(day_data['failed'])
            
            avg_score = round(sum(day_data['scores']) / len(day_data['scores']), 1) if day_data['scores'] else 0
            chart_avg_scores.append(avg_score)
        
        # Difficulty distribution
        difficulty_query = all_attempts.values('test__difficulty').annotate(
            count=Count('id'),
            avg_score=Avg('score'),
            pass_count=Count('id', filter=Q(passed=True))
        )
        difficulty_label_map = dict(SkillTest.DIFFICULTY_LEVELS)
        difficulty_stats = []
        for entry in difficulty_query:
            count = entry['count']
            avg_score = float(entry['avg_score']) if entry['avg_score'] is not None else 0
            pass_count = entry.get('pass_count') or 0
            difficulty_stats.append({
                'difficulty': entry['test__difficulty'],
                'label': difficulty_label_map.get(entry['test__difficulty'], entry['test__difficulty'].title()),
                'count': count,
                'avg_score': round(avg_score, 1),
                'pass_rate': round((pass_count / count) * 100, 1) if count else 0,
                'pass_count': pass_count
            })
        
        # Recent streak analysis
        streak = 0
        max_streak = 0
        for attempt in all_attempts.order_by('-completed_at'):
            if attempt.passed:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        
        # Improvement trends
        improvement_data = {}
        for skill, stats in skill_stats.items():
            attempts = sorted(stats['attempts'], key=lambda a: a.completed_at)
            if len(attempts) >= 2:
                first_score = attempts[0].score or 0
                last_score = attempts[-1].score or 0
                improvement_data[skill] = {
                    'first': first_score,
                    'last': last_score,
                    'change': last_score - first_score,
                    'trend': 'improving' if last_score > first_score else 'declining' if last_score < first_score else 'stable'
                }
        
        context.update({
            # Main data
            'passed_attempts': passed_attempts,
            'failed_attempts': failed_attempts,
            'all_attempts': all_attempts,
            
            # Overall stats
            'total_attempts': total_attempts,
            'total_passed': total_passed,
            'total_failed': total_attempts - total_passed,
            'overall_pass_rate': round((total_passed / total_attempts * 100), 1) if total_attempts > 0 else 0,
            'total_time_spent': total_time_spent,
            'avg_score': round(all_attempts.aggregate(avg=Avg('score'))['avg'] or 0, 1),
            'unique_skills_tested': len(skill_stats),
            
            # Skill breakdown
            'skill_stats': dict(skill_stats),
            
            # Chart data
            'chart_data': json.dumps({
                'labels': chart_labels,
                'passed': chart_passed,
                'failed': chart_failed,
                'avg_scores': chart_avg_scores
            }),
            
            # Difficulty stats
            'difficulty_stats': difficulty_stats,
            
            # Streaks
            'current_streak': streak,
            'max_streak': max_streak,
            
            # Improvements
            'improvement_data': improvement_data,
            
            # Badges
            'total_badges': SkillBadge.objects.filter(user=user).count(),
        })
        
        return context


def _build_group_challenge_form(group):
    form = GroupChallengeForm()
    form.fields['test'].queryset = SkillTest.objects.filter(
        skill_name__iexact=group.skill_focus,
        is_active=True
    )
    return form


class StudyGroupListView(LoginRequiredMixin, PersonalAccountRequiredMixin, ListView):
    model = StudyGroup
    template_name = 'assessments/study_groups.html'
    context_object_name = 'groups'
    paginate_by = 12

    def get_queryset(self):
        skill = self.request.GET.get('skill')
        qs = StudyGroup.objects.filter(is_public=True).prefetch_related('memberships__user')
        if skill:
            qs = qs.filter(skill_focus__icontains=skill)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filters'] = {
            'skill': self.request.GET.get('skill', '')
        }
        context['skills'] = StudyGroup.objects.values_list('skill_focus', flat=True).distinct()
        context['my_groups'] = self.request.user.study_groups.all()
        return context


class CreateStudyGroupView(LoginRequiredMixin, PersonalAccountRequiredMixin, CreateView):
    model = StudyGroup
    template_name = 'assessments/create_study_group.html'
    fields = ['name', 'description', 'skill_focus', 'is_public', 'max_members']

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        StudyGroupMembership.objects.create(
            user=self.request.user,
            group=self.object,
            role='ADMIN'
        )
        messages.success(self.request, 'Study group created successfully!')
        return response


class JoinStudyGroupView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    def post(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)
        if group.members.count() >= group.max_members:
            messages.error(request, 'This study group is full.')
            return redirect('assessments:study_group_detail', group_id=group_id)

        membership, created = StudyGroupMembership.objects.get_or_create(
            user=request.user,
            group=group,
            defaults={'role': 'MEMBER'}
        )

        if not created:
            messages.info(request, 'You are already a member of this group.')
        else:
            messages.success(request, f'Joined {group.name}!')
        return redirect('assessments:study_group_detail', group_id=group_id)


class LeaveStudyGroupView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    def post(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)
        membership = StudyGroupMembership.objects.filter(user=request.user, group=group).first()
        if not membership:
            messages.error(request, 'You are not part of this group.')
            return redirect('assessments:study_group_detail', group_id=group_id)

        if membership.role == 'ADMIN' and group.memberships.filter(role='ADMIN').count() <= 1:
            messages.error(request, 'At least one admin must remain in the group.')
            return redirect('assessments:study_group_detail', group_id=group_id)

        membership.delete()
        messages.success(request, f'You left {group.name}.')
        return redirect('assessments:study_groups')


class StudyGroupDetailView(LoginRequiredMixin, PersonalAccountRequiredMixin, DetailView):
    model = StudyGroup
    template_name = 'assessments/study_group_detail.html'
    context_object_name = 'group'
    pk_url_kwarg = 'group_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        membership = StudyGroupMembership.objects.filter(user=self.request.user, group=group).first()

        challenges = group.challenges.order_by('-start_date')
        active_challenge = challenges.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now()).first()
        discussions = QuestionDiscussion.objects.filter(
            question__skill_name__iexact=group.skill_focus
        ).select_related('user').order_by('-created_at')[:5]

        context.update({
            'membership': membership,
            'is_member': bool(membership),
            'is_admin': membership.role == 'ADMIN' if membership else False,
            'members': group.members.select_related('personal_profile').all(),
            'member_count': group.members.count(),
            'challenges': challenges,
            'active_challenge': active_challenge,
            'discussions': discussions,
            'challenge_form': _build_group_challenge_form(group),
        })
        return context


class CreateGroupChallengeView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    form_class = GroupChallengeForm

    def post(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)
        membership = StudyGroupMembership.objects.filter(user=request.user, group=group, role='ADMIN').first()
        if not membership:
            messages.error(request, 'Only group admins can create challenges.')
            return redirect('assessments:study_group_detail', group_id=group_id)

        form = self.form_class(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.group = group
            challenge.save()
            messages.success(request, 'Group challenge created successfully.')
        else:
            messages.error(request, 'Unable to create challenge. Please check the inputs.')
        return redirect('assessments:group_leaderboard', group_id=group_id)


class GroupLeaderboardView(LoginRequiredMixin, PersonalAccountRequiredMixin, TemplateView):
    template_name = 'assessments/group_challenge.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_object_or_404(StudyGroup, id=self.kwargs.get('group_id'))
        challenges = group.challenges.order_by('-start_date')
        selected_id = self.request.GET.get('challenge')
        challenge = challenges.filter(id=selected_id).first() if selected_id else challenges.first()
        leaderboard = challenge.get_leaderboard() if challenge else []
        membership = StudyGroupMembership.objects.filter(user=self.request.user, group=group).first()

        context.update({
            'group': group,
            'challenges': challenges,
            'selected_challenge': challenge,
            'leaderboard': leaderboard,
            'is_admin': membership and membership.role == 'ADMIN',
            'challenge_form': _build_group_challenge_form(group)
        })
        return context


class QuestionDiscussionView(LoginRequiredMixin, PersonalAccountRequiredMixin, TemplateView):
    template_name = 'assessments/question_discussion.html'

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(QuestionPool, id=kwargs.get('question_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        discussions = QuestionDiscussion.objects.filter(
            question=self.question
        ).annotate(
            upvotes_count=Count('upvotes')
        ).order_by('-upvotes_count', '-created_at')
        context.update({
            'question': self.question,
            'discussion_form': DiscussionForm(),
            'discussions': discussions,
            'explanation_votes': self.question.explanation_upvotes or {},
            'is_flagged': self.question.is_flagged,
        })
        return context

    def post(self, request, *args, **kwargs):
        form = DiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.user = request.user
            discussion.question = self.question
            discussion.save()
            messages.success(request, 'Comment added!')
            return redirect('assessments:question_discussion', question_id=self.question.id)
        messages.error(request, 'Unable to add comment.')
        return self.get(request, *args, **kwargs)


class UpvoteExplanationView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    def post(self, request, question_id):
        if getattr(request, 'limited', False):
            return render_rate_limit(request, '30 flags per hour')
        question = get_object_or_404(QuestionPool, id=question_id)
        target = request.POST.get('target', 'primary')
        action = request.POST.get('action', 'upvote')
        votes = question.explanation_upvotes or {}
        entry = votes.get(target, {'upvotes': 0, 'downvotes': 0})
        if action == 'upvote':
            entry['upvotes'] += 1
        else:
            entry['downvotes'] += 1
        votes[target] = entry
        question.explanation_upvotes = votes
        question.save(update_fields=['explanation_upvotes'])
        return JsonResponse({'votes': entry})


@method_decorator(ratelimit(key='ip', rate='30/h', method='POST', block=False), name='dispatch')
class FlagQuestionView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    def post(self, request, question_id):
        if getattr(request, 'limited', False):
            return render_rate_limit(request, '30 flags per hour')

        question = get_object_or_404(QuestionPool, id=question_id)
        question.flag_count += 1
        question.is_flagged = question.flag_count > 0
        question.save(update_fields=['flag_count', 'is_flagged'])
        if question.flag_count > 5:
            logger.warning(f'Question {question.id} flagged {question.flag_count} times.')
            try:
                link = request.build_absolute_uri(reverse('assessments:question_discussion', kwargs={'question_id': question.id}))
            except Exception:
                link = 'N/A'
            mail_admins(
                subject=f'Question {question.id} highly flagged',
                message=(
                    f'Question {question.id} ({question.skill_name}) has been flagged {question.flag_count} times.\n'
                    f'Submitted by {request.user.get_full_name() or request.user.email} ({request.user.email}).\n'
                    f'View discussion: {link}'
                )
            )
        return JsonResponse({'flag_count': question.flag_count, 'is_flagged': question.is_flagged})


class BookmarkQuestionView(LoginRequiredMixin, PersonalAccountRequiredMixin, View):
    def post(self, request, question_id):
        question = get_object_or_404(QuestionPool, id=question_id, is_active=True)
        attempt_id = request.POST.get('attempt_id')
        notes = request.POST.get('notes', '').strip()
        attempt = None
        if attempt_id:
            attempt = SkillAssessmentAttempt.objects.filter(id=attempt_id, user=request.user).first()

        bookmark, created = BookmarkedQuestion.objects.get_or_create(
            user=request.user,
            question=question,
            defaults={'attempt': attempt, 'notes': notes}
        )

        if not created:
            updated = False
            if notes and bookmark.notes != notes:
                bookmark.notes = notes
                updated = True
            if attempt and bookmark.attempt != attempt:
                bookmark.attempt = attempt
                updated = True
            if updated:
                bookmark.save(update_fields=['notes', 'attempt'])

        return JsonResponse({
            'success': True,
            'created': created,
            'notes': bookmark.notes,
            'bookmark_id': str(bookmark.id)
        })


class MyBookmarksView(LoginRequiredMixin, PersonalAccountRequiredMixin, ListView):
    model = BookmarkedQuestion
    template_name = 'assessments/my_bookmarks.html'
    context_object_name = 'bookmarks'
    paginate_by = 12

    def get_queryset(self):
        qs = BookmarkedQuestion.objects.filter(user=self.request.user).select_related('question').order_by('-created_at')
        skill = self.request.GET.get('skill')
        if skill:
            qs = qs.filter(question__skill_name__icontains=skill)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        skill_filter = self.request.GET.get('skill', '')
        context.update({
            'filters': {'skill': skill_filter},
            'skills': BookmarkedQuestion.objects.filter(user=self.request.user).values_list('question__skill_name', flat=True).distinct().order_by('question__skill_name'),
            'total_bookmarks': context['page_obj'].paginator.count if context.get('page_obj') else 0
        })
        return context


class CreateCustomPracticeView(LoginRequiredMixin, PersonalAccountRequiredMixin, TemplateView):
    template_name = 'assessments/custom_practice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookmarks = self._bookmarks()
        skill_filter = self.request.GET.get('skill', '')
        if skill_filter:
            bookmarks = bookmarks.filter(question__skill_name__icontains=skill_filter)
        context.update({
            'bookmarks': bookmarks,
            'filters': {'skill': skill_filter},
            'skills': self._bookmarks().values_list('question__skill_name', flat=True).distinct().order_by('question__skill_name'),
            'total_bookmarks': bookmarks.count()
        })
        return context

    def post(self, request, *args, **kwargs):
        selected_ids = request.POST.getlist('bookmarks')
        if not selected_ids:
            messages.error(request, 'Select at least one bookmark to create a practice test.')
            return redirect('assessments:custom_practice')

        bookmarks = self._bookmarks().filter(id__in=selected_ids)
        if not bookmarks.exists():
            messages.error(request, 'No valid bookmarks selected.')
            return redirect('assessments:custom_practice')

        attempt = self._build_custom_attempt(bookmarks)
        if attempt:
            messages.success(request, 'Custom practice session is ready!')
            return redirect('assessments:take', attempt_id=attempt.id)

        messages.error(request, 'Unable to create a custom practice session at this time.')
        return redirect('assessments:custom_practice')

    def _bookmarks(self):
        return BookmarkedQuestion.objects.filter(user=self.request.user).select_related('question')

    def _build_custom_attempt(self, bookmarks):
        question_payloads = []
        for bookmark in bookmarks:
            question = bookmark.question
            payload = {
                'id': str(question.id),
                'type': question.question_type.lower(),
                'question': question.question,
                'options': question.options or [],
                'correct_answer': question.correct_answer,
                'points': question.points,
                'estimated_time': question.estimated_time_seconds,
                'explanation': question.explanation
            }
            question_payloads.append(payload)

        if not question_payloads:
            return None

        test = get_or_create_custom_practice_test()
        attempt = SkillAssessmentAttempt.objects.create(
            user=self.request.user,
            test=test,
            frozen_questions=question_payloads,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
            is_practice_mode=True
        )
        return attempt

class LearningPathView(LoginRequiredMixin, PersonalAccountRequiredMixin, TemplateView):
    template_name = 'assessments/learning_path.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        generator = LearningPathGenerator(self.request.user)
        path_data = generator.generate_path()

        context.update({
            'weak_areas': path_data['weak_areas'],
            'next_steps': path_data['next_steps'],
            'mastered_skills': path_data['mastered_skills'],
            'study_plan': path_data['study_plan'],
            'radar_data': path_data['radar_data']
        })
        return context


class AnalyticsView(LoginRequiredMixin, PersonalAccountRequiredMixin, TemplateView):
    template_name = 'assessments/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analytics = AssessmentAnalytics(self.request.user)
        time_analysis = analytics.get_time_analysis()
        difficulty_progression = analytics.get_difficulty_progression()
        question_type_performance = analytics.get_question_type_performance()
        radar_payload = json.dumps(analytics.get_skill_radar_data())
        time_payload = json.dumps({
            'labels': [entry['bucket'] for entry in time_analysis],
            'avg_scores': [entry['avg_score'] for entry in time_analysis],
            'pass_rates': [entry['pass_rate'] for entry in time_analysis]
        })
        difficulty_payload = json.dumps({
            'labels': [entry['label'] for entry in difficulty_progression],
            'avg_scores': [entry['avg_score'] for entry in difficulty_progression],
            'pass_rates': [entry['pass_rate'] for entry in difficulty_progression]
        })
        question_type_payload = json.dumps({
            'labels': [entry['label'] for entry in question_type_performance],
            'pass_rates': [entry['pass_rate'] for entry in question_type_performance]
        })
        best_time_bucket = max(time_analysis, key=lambda x: x['pass_rate']) if time_analysis else {'bucket': 'Unknown', 'pass_rate': 0}

        context.update({
            'time_analysis': time_analysis,
            'difficulty_progression': difficulty_progression,
            'question_type_performance': question_type_performance,
            'radar_payload': radar_payload,
            'time_payload': time_payload,
            'difficulty_payload': difficulty_payload,
            'question_type_payload': question_type_payload,
            'improvement_rate': analytics.get_improvement_rate(),
            'consistency_score': analytics.get_consistency_score(),
            'insights': analytics.generate_insights(),
            'total_attempts': len(analytics.attempts),
            'best_time_bucket': best_time_bucket
        })
        return context


class LeaderboardView(LoginRequiredMixin, PersonalAccountRequiredMixin, TemplateView):
    template_name = 'assessments/leaderboard.html'
    TIMEFRAME_WINDOWS = {
        'weekly': timedelta(days=7),
        'monthly': timedelta(days=30),
        'all_time': None
    }
    LEADERBOARD_LIMIT = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tabs = list(self.TIMEFRAME_WINDOWS.keys())
        leaderboard_labels = {'weekly': 'Weekly', 'monthly': 'Monthly', 'all_time': 'All Time'}

        global_boards = {
            timeframe: self._build_leaderboard(self._attempts_for_timeframe(timeframe))
            for timeframe in tabs
        }
        skill_boards = {
            timeframe: self._build_skill_leaderboard(self._attempts_for_timeframe(timeframe))
            for timeframe in tabs
        }

        achievements = Achievement.objects.all()
        user_achievements = {
            ua.achievement.code: ua
            for ua in UserAchievement.objects.filter(user=self.request.user)
        }
        achievements_data = []
        for achievement in achievements:
            earned = achievement.code in user_achievements
            achievements_data.append({
                'code': achievement.code,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'earned': earned,
                'earned_at': user_achievements[achievement.code].earned_at if earned else None,
                'progress': 100 if earned else 0
            })

        context.update({
            'leaderboard_tabs': tabs,
            'leaderboard_labels': leaderboard_labels,
            'global_leaderboards': global_boards,
            'skill_leaderboards': skill_boards,
            'achievements': achievements_data,
            'recent_achievements': sorted(
                user_achievements.values(),
                key=lambda ua: ua.earned_at,
                reverse=True
            )[:4]
        })
        return context

    def _attempts_for_timeframe(self, timeframe):
        window = self.TIMEFRAME_WINDOWS.get(timeframe)
        qs = SkillAssessmentAttempt.objects.filter(status='COMPLETED')
        if window:
            cutoff = timezone.now() - window
            qs = qs.filter(completed_at__gte=cutoff)
        return qs

    def _build_leaderboard(self, queryset):
        aggregated = queryset.values(
            'user',
            'user__email',
            'user__personal_profile__full_name'
        ).annotate(
            avg_score=Avg('score'),
            best_score=Max('score'),
            attempts=Count('id'),
            passed=Count('id', filter=Q(passed=True))
        ).order_by('-avg_score', '-best_score')[:self.LEADERBOARD_LIMIT]

        user_ids = [entry['user'] for entry in aggregated]
        badge_counts = dict(
            SkillBadge.objects.filter(user_id__in=user_ids)
            .values('user_id')
            .annotate(count=Count('id'))
            .values_list('user_id', 'count')
        )

        entries = []
        for rank, entry in enumerate(aggregated, start=1):
            user_id = entry['user']
            entries.append({
                'rank': rank,
                'name': entry.get('user__personal_profile__full_name') or entry.get('user__email'),
                'avg_score': round(entry['avg_score'] or 0, 1),
                'best_score': entry['best_score'] or 0,
                'attempts': entry['attempts'],
                'passed': entry['passed'],
                'badges': badge_counts.get(user_id, 0),
                'streak': self._calculate_streak(user_id),
                'user_id': user_id
            })
        return entries

    def _build_skill_leaderboard(self, queryset):
        skill_counts = queryset.values('test__skill_name').annotate(total=Count('id')).order_by('-total')[:4]
        skills = [entry['test__skill_name'] for entry in skill_counts]
        boards = []
        for skill in skills:
            skill_qs = queryset.filter(test__skill_name=skill)
            boards.append({
                'skill': skill,
                'entries': self._build_leaderboard(skill_qs)
            })
        return boards

    def _calculate_streak(self, user_id):
        attempts = SkillAssessmentAttempt.objects.filter(
            user_id=user_id,
            status='COMPLETED'
        ).order_by('-completed_at')[:5]
        streak = 0
        for attempt in attempts:
            if attempt.passed:
                streak += 1
            else:
                break
        return streak
