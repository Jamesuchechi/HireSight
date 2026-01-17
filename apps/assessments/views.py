from django.views.generic import ListView, DetailView, CreateView, UpdateView
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
import logging

from .models import (
    SkillTest, SkillAssessmentAttempt, SkillBadge, 
    AssessmentCategory, QuestionPool
)
from .forms import TestFilterForm
from .utils import generate_certificate_pdf, get_client_ip

logger = logging.getLogger(__name__)


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
            tests_data.append({
                'test': test,
                'best_score': best_scores.get(str(test.id)),
                'has_badge': test.id in user_badges,
                'matches_skills': test.matches_user_skills(self.request.user)
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
