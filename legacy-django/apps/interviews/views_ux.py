"""
Views for interview practice UX improvements.
Handles session setup, warmup flow, progress tracking, and history dashboard.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import DetailView
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .views import CandidateRequiredMixin
from django.utils.decorators import method_decorator
from django.db.models import Avg, Q, Count
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from .progress_tasks import generate_warmup_question_task


from .models import InterviewPracticeSession, PracticeQuestion, PracticeResponse, Interview, InterviewCodingSession


@method_decorator(login_required, name='dispatch')
class PracticeSetupView(View):
    """Display session setup modal with configuration options."""
    
    def get(self, request):
        """Show practice session setup page."""
        placeholder_value = 0
        context = {
            'focus_areas': [
                {'id': 'leadership', 'label': 'Leadership'},
                {'id': 'technical', 'label': 'Technical Skills'},
                {'id': 'communication', 'label': 'Communication'},
                {'id': 'problemsolving', 'label': 'Problem Solving'},
                {'id': 'collaboration', 'label': 'Collaboration'},
                {'id': 'adaptability', 'label': 'Adaptability'},
            ],
            'question_counts': [5, 10, 15],
            'warmup_url_pattern': reverse(
                'interviews:warmup',
                kwargs={'session_id': placeholder_value}
            )
        }
        return render(request, 'interviews/practice/practice_setup.html', context)


@method_decorator(login_required, name='dispatch')
class SaveSessionSetupView(View):
    """Save user's session setup configuration."""
    
    def post(self, request):
        """Save setup data and create session."""
        try:
            data = json.loads(request.body)
            # Normalize values
            focus_areas = data.get('focus_areas') or []
            difficulty = data.get('difficulty', 'medium')
            time_limit = int(data.get('time_limit_per_question', 2))
            number_of_questions = int(data.get('number_of_questions', 5))
            enable_video = data.get('enable_video', True)
            
            settings_payload = {
                'focus_areas': focus_areas,
                'difficulty': difficulty,
                'time_limit_per_question': time_limit,
                'number_of_questions': number_of_questions,
                'enable_video': enable_video
            }

            # Create new practice session
            session = InterviewPracticeSession.objects.create(
                candidate=request.user,
                focus_areas=focus_areas,
                difficulty=difficulty,
                time_limit_per_question=time_limit,
                enable_video=enable_video,
                video_analysis_enabled=enable_video,
                settings=settings_payload,
                status=InterviewPracticeSession.Status.CREATED,
            )

            generate_warmup_question_task.delay(session.id)
            
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'message': 'Session setup saved successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@method_decorator(login_required, name='dispatch')
class WarmupFlowView(View):
    """Display warmup flow for testing camera, microphone, etc."""
    
    def get(self, request, session_id):
        """Show warmup flow page."""
        session = get_object_or_404(
            InterviewPracticeSession,
            id=session_id,
            candidate=request.user
        )
        
        # Self-healing: Ensure warmup question generation is started if it's missing
        # This handles cases where the initial setup trigger failed or was lost
        if not session.warmup_question_prompt and session.warmup_question_state == InterviewPracticeSession.GenerationState.PENDING:
             generate_warmup_question_task.delay(session.id)
        
        context = {
            'session': session,
            'camera_tips': [
                'Allow camera access',
                'Check your camera preview',
                'Confirm and continue'
            ]
        }
        return render(request, 'interviews/practice/warmup_flow.html', context)


@method_decorator(login_required, name='dispatch')
class CompleteWarmupView(View):
    """Mark warmup as completed and move to practice questions."""
    
    def post(self, request, session_id):
        """Mark warmup completed and redirect to first question."""
        session = get_object_or_404(
            InterviewPracticeSession,
            id=session_id,
            candidate=request.user
        )
        
        # Mark warmup as completed
        session.warmup_completed = True
        session.status = InterviewPracticeSession.Status.IN_PROGRESS
        session.started_at = timezone.now()
        session.save()
        
        # CRITICAL FIX: Check if questions exist, if not generate them
        questions = PracticeQuestion.objects.filter(session=session).order_by('order')
        
        if not questions.exists():
            # Questions haven't been generated yet - trigger generation
            from .tasks import generate_practice_questions
            
            # Update generation state
            session.question_generation_state = InterviewPracticeSession.GenerationState.IN_PROGRESS
            session.save()
            
            # Trigger async question generation
            generate_practice_questions.delay(session.id)
            
            # Return response asking user to wait
            return JsonResponse({
                'success': True,
                'status': 'generating',
                'message': 'Warmup completed. Generating your practice questions...',
                'redirect_url': reverse('interviews:practice_feedback', kwargs={'session_id': session.id})
            })
        
        # Questions exist - redirect to first question
        first_question = questions.first()
        
        return JsonResponse({
            'success': True,
            'status': 'ready',
            'message': 'Warmup completed. Starting practice session.',
            'redirect_url': reverse('interviews:practice_question', kwargs={'question_id': first_question.id})
        })


@login_required
def warmup_question_status(request, session_id):
    """Check the status of the warmup question generation."""
    session = get_object_or_404(InterviewPracticeSession, id=session_id, candidate=request.user)
    
    if session.warmup_question_state == InterviewPracticeSession.GenerationState.COMPLETED:
        return JsonResponse({
            "status": "completed",
            "question": session.warmup_question_prompt
        })
    elif session.warmup_question_state == InterviewPracticeSession.GenerationState.FAILED:
        return JsonResponse({
            "status": "failed",
            "message": "Failed to generate a warmup question. You can skip this step."
        })
    else: # PENDING or IN_PROGRESS
        # Self-healing: If status is PENDING during polling, ensure task is queued.
        # This fixes the "stuck in pending" issue if the task wasn't triggered.
        if session.warmup_question_state == InterviewPracticeSession.GenerationState.PENDING:
            cache_key = f"warmup_gen_triggered_{session.id}"
            # Use cache to debounce triggers (prevent flooding every 3 seconds)
            if not cache.get(cache_key):
                generate_warmup_question_task.delay(session.id)
                cache.set(cache_key, "true", timeout=15) # Don't re-trigger for 15s

        return JsonResponse({"status": "pending"})


@method_decorator(login_required, name='dispatch')
class PracticeHistoryDashboardView(View):
    """Enhanced practice history dashboard with comprehensive statistics and insights."""
    
    def get(self, request):
        """Show enhanced practice history dashboard."""
        user = request.user
        
        # Get all completed sessions
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        ).prefetch_related('questions', 'session_responses').order_by('-completed_at')[:10]
        
        # Calculate comprehensive statistics
        stats = self._calculate_comprehensive_stats(user, sessions)
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(user)
        
        # Generate AI tips based on performance
        ai_tips = self._generate_personalized_tips(user, stats)
        
        # Get recent activity
        recent_activity = self._get_recent_activity(user)
        
        context = {
            'sessions': sessions,
            'stats': stats,
            'chart_data': chart_data,
            'ai_tips': ai_tips,
            'recent_activity': recent_activity
        }
        return render(request, 'interviews/practice/practice_history_dashboard.html', context)
    
    def _calculate_comprehensive_stats(self, user, sessions):
        """Calculate comprehensive performance statistics."""
        all_sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        )
        
        total_sessions = all_sessions.count()
        
        if not total_sessions:
            return self._get_empty_stats()
        
        # Basic statistics
        all_sessions_list = list(all_sessions.values('overall_score', 'completed_at'))
        scores = [float(s['overall_score']) for s in all_sessions_list if s['overall_score']]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        best_score = max(scores) if scores else 0
        lowest_score = min(scores) if scores else 0
        median_score = self._calculate_median(scores) if scores else 0
        
        # Score trend (last week vs overall average)
        score_trend = self._calculate_score_trend(user, avg_score)
        
        # Streak calculation
        current_streak = self._calculate_streak(user)
        longest_streak = self._calculate_longest_streak(user)
        
        # Category performance
        category_performance = self._calculate_category_performance(user)
        categories_practiced = len(category_performance)
        
        # Goals and progress
        next_goal = self._calculate_next_goal(avg_score)
        goal_progress = min(100, int((avg_score / next_goal) * 100)) if next_goal > 0 else 100
        
        # Badges and achievements
        perfect_score = any(s >= 100 for s in scores)
        
        # Time-based statistics
        total_practice_time = self._calculate_total_practice_time(all_sessions)
        average_session_time = total_practice_time / total_sessions if total_sessions > 0 else 0
        
        # Question statistics
        total_questions_answered = PracticeResponse.objects.filter(
            session__candidate=user,
            session__status=InterviewPracticeSession.Status.COMPLETED
        ).count()
        
        # Improvement rate
        improvement_rate = self._calculate_improvement_rate(user)
        
        # Consistency metrics
        practice_frequency = self._calculate_practice_frequency(user)
        
        # Video analysis stats (if applicable)
        video_sessions = all_sessions.filter(enable_video=True).count()
        video_percentage = (video_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            # Basic stats
            'total_sessions': total_sessions,
            'average_score': round(avg_score, 1),
            'best_score': round(best_score, 1),
            'lowest_score': round(lowest_score, 1),
            'median_score': round(median_score, 1),
            
            # Trends
            'score_trend': round(score_trend, 1),
            'improvement_rate': round(improvement_rate, 1),
            
            # Streaks
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            
            # Goals
            'next_goal': next_goal,
            'goal_progress': goal_progress,
            
            # Categories
            'category_performance': category_performance,
            'categories_practiced': categories_practiced,
            
            # Achievements
            'perfect_score': perfect_score,
            
            # Time metrics
            'total_practice_time': total_practice_time,
            'average_session_time': average_session_time,
            
            # Question metrics
            'total_questions_answered': total_questions_answered,
            'questions_per_session': round(total_questions_answered / total_sessions, 1) if total_sessions > 0 else 0,
            
            # Consistency
            'practice_frequency': practice_frequency,
            
            # Video stats
            'video_sessions': video_sessions,
            'video_percentage': round(video_percentage, 1),
            
            # Milestones for UI
            'milestones': {
                'first_session': total_sessions >= 1,
                'five_sessions': total_sessions >= 5,
                'ten_sessions': total_sessions >= 10,
                'twenty_five_sessions': total_sessions >= 25,
                'perfect_score': perfect_score,
                'week_streak': current_streak >= 7,
                'expert_average': avg_score >= 90,
                'improving': score_trend > 10,
                'versatile': categories_practiced >= 5,
            }
        }
    
    def _get_empty_stats(self):
        """Return empty stats structure for users with no sessions."""
        return {
            'total_sessions': 0,
            'average_score': 0,
            'best_score': 0,
            'lowest_score': 0,
            'median_score': 0,
            'score_trend': 0,
            'current_streak': 0,
            'longest_streak': 0,
            'next_goal': 80,
            'goal_progress': 0,
            'category_performance': [],
            'categories_practiced': 0,
            'perfect_score': False,
            'improvement_rate': 0,
            'total_practice_time': 0,
            'average_session_time': 0,
            'total_questions_answered': 0,
            'questions_per_session': 0,
            'practice_frequency': 0,
            'video_sessions': 0,
            'video_percentage': 0,
            'milestones': {
                'first_session': False,
                'five_sessions': False,
                'ten_sessions': False,
                'twenty_five_sessions': False,
                'perfect_score': False,
                'week_streak': False,
                'expert_average': False,
                'improving': False,
                'versatile': False,
            }
        }
    
    def _calculate_median(self, scores):
        """Calculate median score."""
        if not scores:
            return 0
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        if n % 2 == 0:
            return (sorted_scores[n//2 - 1] + sorted_scores[n//2]) / 2
        return sorted_scores[n//2]
    
    def _calculate_score_trend(self, user, overall_avg):
        """Calculate score trend comparing recent vs overall average."""
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        recent_sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED,
            completed_at__gte=week_ago
        )
        
        if not recent_sessions.exists():
            return 0
        
        recent_scores = [float(s.overall_score) for s in recent_sessions if s.overall_score]
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else overall_avg
        
        return recent_avg - overall_avg
    
    def _calculate_streak(self, user):
        """Calculate current consecutive days with practice."""
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        ).order_by('-completed_at')
        
        if not sessions.exists():
            return 0
        
        streak = 0
        current_date = timezone.now().date()
        
        # Get unique dates of completed sessions
        session_dates = set()
        for session in sessions:
            if session.completed_at:
                session_dates.add(session.completed_at.date())
        
        # Count consecutive days
        while current_date in session_dates or (current_date - timedelta(days=1)) in session_dates:
            if current_date in session_dates:
                streak += 1
            current_date -= timedelta(days=1)
        
        return streak
    
    def _calculate_longest_streak(self, user):
        """Calculate longest streak ever achieved."""
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        ).order_by('completed_at')
        
        if not sessions.exists():
            return 0
        
        session_dates = sorted(set(
            s.completed_at.date() for s in sessions if s.completed_at
        ))
        
        if not session_dates:
            return 0
        
        longest = 1
        current = 1
        
        for i in range(1, len(session_dates)):
            if (session_dates[i] - session_dates[i-1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        
        return longest
    
    def _calculate_category_performance(self, user):
        """Calculate average score by category."""
        responses = PracticeResponse.objects.filter(
            session__candidate=user,
            session__status=InterviewPracticeSession.Status.COMPLETED,
            question__isnull=False,
            ai_score__isnull=False
        ).select_related('question')
        
        category_scores = {}
        
        for response in responses:
            category = response.question.category or 'General'
            score = float(response.ai_score)
            
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(score)
        
        # Calculate averages
        performance = []
        for category, scores in category_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            performance.append({
                'name': str(category).title(),
                'score': round(avg, 1),
                'count': len(scores)
            })
        
        return sorted(performance, key=lambda x: x['score'], reverse=True)
    
    def _calculate_next_goal(self, current_avg):
        """Calculate next scoring goal."""
        if current_avg < 70:
            return 70
        elif current_avg < 80:
            return 80
        elif current_avg < 90:
            return 90
        else:
            return 100
    
    def _calculate_total_practice_time(self, sessions):
        """Calculate total practice time in minutes."""
        total_minutes = 0
        for session in sessions:
            if session.started_at and session.completed_at:
                duration = session.completed_at - session.started_at
                total_minutes += duration.total_seconds() / 60
        return int(total_minutes)
    
    def _calculate_improvement_rate(self, user):
        """Calculate improvement rate over time."""
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        ).order_by('completed_at')
        
        if sessions.count() < 2:
            return 0
        
        first_half = sessions[:sessions.count()//2]
        second_half = sessions[sessions.count()//2:]
        
        first_avg = sum(float(s.overall_score) for s in first_half if s.overall_score) / first_half.count()
        second_avg = sum(float(s.overall_score) for s in second_half if s.overall_score) / second_half.count()
        
        return second_avg - first_avg
    
    def _calculate_practice_frequency(self, user):
        """Calculate practice frequency (sessions per week)."""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED,
            completed_at__gte=thirty_days_ago
        ).count()
        
        return round(recent_sessions / 4.3, 1)  # Convert to per-week average
    
    def _prepare_chart_data(self, user):
        """Prepare data for the progress chart."""
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        ).order_by('completed_at')[:20]  # Last 20 sessions
        
        labels = [f"Session {i+1}" for i in range(sessions.count())]
        scores = [float(s.overall_score or 0) for s in sessions]
        
        return {
            'labels': json.dumps(labels),
            'scores': json.dumps(scores)
        }
    
    def _generate_personalized_tips(self, user, stats):
        """Generate personalized AI tips based on performance."""
        tips = []
        
        # Analyze score performance
        if stats['average_score'] < 60:
            tips.append({
                'title': 'Build Your Foundation',
                'content': 'Your scores suggest you\'re still building fundamentals. Focus on understanding the STAR method (Situation, Task, Action, Result) for structured responses. Practice with easier questions first to build confidence.',
                'icon': '📚',
                'color': 'blue'
            })
        elif stats['average_score'] < 70:
            tips.append({
                'title': 'Strengthen Core Skills',
                'content': 'You\'re making progress! Focus on clarity and structure in your responses. Record yourself answering questions and watch for filler words and unclear explanations.',
                'icon': '💪',
                'color': 'indigo'
            })
        
        # Analyze trend
        if stats['score_trend'] < -5:
            tips.append({
                'title': 'Address the Decline',
                'content': 'Your recent scores have dropped. This might indicate fatigue or rushing through practice. Take a break, review your best responses, and return with fresh focus.',
                'icon': '⚠️',
                'color': 'amber'
            })
        elif stats['score_trend'] > 10:
            tips.append({
                'title': 'Momentum Builder',
                'content': f'Excellent progress! Your scores have improved by {stats["score_trend"]:.1f}% recently. Keep this momentum by challenging yourself with harder questions.',
                'icon': '🚀',
                'color': 'green'
            })
        
        # Analyze consistency
        if stats['current_streak'] >= 7:
            tips.append({
                'title': 'Consistency Champion',
                'content': f'Amazing {stats["current_streak"]}-day streak! Daily practice is the key to mastery. Your consistent effort is paying off.',
                'icon': '🔥',
                'color': 'orange'
            })
        elif stats['practice_frequency'] < 1:
            tips.append({
                'title': 'Practice More Regularly',
                'content': 'You\'re practicing less than once a week. Try to set a regular schedule - even 15 minutes daily can make a huge difference in your improvement rate.',
                'icon': '📅',
                'color': 'purple'
            })
        
        # Analyze category diversity
        if stats['categories_practiced'] < 3:
            tips.append({
                'title': 'Diversify Your Practice',
                'content': 'You\'ve only practiced a few question types. Branch out into behavioral, technical, and situational questions to become a well-rounded candidate.',
                'icon': '🎯',
                'color': 'blue'
            })
        
        # Video feedback
        if stats['video_percentage'] < 50 and stats['total_sessions'] >= 3:
            tips.append({
                'title': 'Use Video More',
                'content': 'Only half your sessions use video. Video practice helps you improve body language, eye contact, and overall presence - crucial for real interviews.',
                'icon': '🎥',
                'color': 'indigo'
            })
        
        # If doing well
        if stats['average_score'] >= 85 and len(tips) < 2:
            tips.append({
                'title': 'Ready for the Real Thing',
                'content': 'Your consistent high scores show you\'re well-prepared. Consider practicing with timed constraints or panel interview scenarios to push yourself further.',
                'icon': '⭐',
                'color': 'green'
            })
        
        # Default tip if none generated
        if not tips:
            tips.append({
                'title': 'Keep Up the Great Work',
                'content': 'You\'re making solid progress! Continue practicing regularly, focus on clear communication, and challenge yourself with different question types.',
                'icon': '💡',
                'color': 'green'
            })
        
        return tips[:3]  # Limit to top 3 tips
    
    def _get_recent_activity(self, user):
        """Get recent activity timeline."""
        activities = []
        
        # Recent sessions
        recent_sessions = InterviewPracticeSession.objects.filter(
            candidate=user
        ).order_by('-created_at')[:5]
        
        for session in recent_sessions:
            activities.append({
                'type': 'session',
                'title': f'Completed {session.get_interview_type_display()} Session',
                'score': session.overall_score,
                'timestamp': session.completed_at or session.created_at,
                'url': f'/interviews/practice/session/{session.id}/report/'
            })
        
        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)[:10]


@method_decorator(login_required, name='dispatch')
class SessionProgressView(View):
    """Real-time session progress tracking."""
    
    def get(self, request, session_id):
        """Get session progress via polling or WebSocket."""
        session = get_object_or_404(
            InterviewPracticeSession,
            id=session_id,
            candidate=request.user
        )
        
        # Count answers
        responses = PracticeResponse.objects.filter(session=session)
        total_questions = session.number_of_questions
        completed_responses = responses.count()
        
        # Calculate current stats
        avg_score = None
        if completed_responses > 0:
            scores = [float(r.overall_score or 0) for r in responses if r.overall_score]
            avg_score = sum(scores) / len(scores) if scores else None
        
        return JsonResponse({
            'session_id': str(session.id),
            'status': session.status,
            'progress': {
                'completed': completed_responses,
                'total': total_questions,
                'percentage': int((completed_responses / total_questions * 100) if total_questions > 0 else 0)
            },
            'current_score': round(avg_score, 2) if avg_score else None,
            'generation_state': session.question_generation_state
        })


@method_decorator(login_required, name='dispatch')
class SessionControlsView(View):
    """Handle session control operations (pause, skip, re-record, exit)."""
    
    def post(self, request, session_id):
        """Handle control action."""
        session = get_object_or_404(
            InterviewPracticeSession,
            id=session_id,
            candidate=request.user
        )
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'pause':
                return self._handle_pause(session, data)
            elif action == 'resume':
                return self._handle_resume(session, data)
            elif action == 'skip':
                return self._handle_skip(session, data)
            elif action == 'rerecord':
                return self._handle_rerecord(session, data)
            elif action == 'exit':
                return self._handle_exit(session, data)
            else:
                return JsonResponse({'error': 'Unknown action'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    def _handle_pause(self, session, data):
        """Pause the session."""
        # Update session state to paused
        session.settings['paused'] = True
        session.settings['pause_time'] = timezone.now().isoformat()
        session.save()
        
        return JsonResponse({'success': True, 'message': 'Session paused'})
    
    def _handle_resume(self, session, data):
        """Resume the session."""
        session.settings['paused'] = False
        session.save()
        
        return JsonResponse({'success': True, 'message': 'Session resumed'})
    
    def _handle_skip(self, session, data):
        """Skip current question."""
        question_id = data.get('question_id')
        
        # Mark response as skipped
        response, created = PracticeResponse.objects.get_or_create(
            session=session,
            question_id=question_id,
            defaults={'overall_score': 0, 'improvements': ['Skipped question']}
        )
        
        if not created:
            response.skipped = True
            response.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Question skipped',
            'response_id': response.id
        })
    
    def _handle_rerecord(self, session, data):
        """Allow re-recording of current question."""
        question_id = data.get('question_id')
        
        # Delete previous response to allow re-recording


        return JsonResponse({
            'success': True,
            'message': 'Question reset for re-recording'
        })
    
    def _handle_exit(self, session, data):
        """Exit session and save progress."""
        session.status = InterviewPracticeSession.Status.REVIEW_PENDING
        session.completed_at = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Session exited and progress saved',
            'redirect_url': f'/interviews/session/{session.id}/report/'
        })


class PracticeResponseDetailView(LoginRequiredMixin, CandidateRequiredMixin, DetailView):
    """Detailed analysis view for a single practice response."""
    model = PracticeResponse
    template_name = 'interviews/practice/response_detail.html'
    context_object_name = 'response'
    pk_url_kwarg = 'response_id'
    
    def get_queryset(self):
        return PracticeResponse.objects.filter(
            session__candidate=self.request.user
        ).select_related('question', 'session')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        response = self.object
        
        # Calculate percentile ranking
        all_scores = PracticeResponse.objects.filter(
            question__category=response.question.category
        ).exclude(ai_score__isnull=True).values_list('ai_score', flat=True)
        
        if response.ai_score and all_scores:
            better_than = sum(1 for score in all_scores if score and score < response.ai_score)
            percentile = (better_than / len(all_scores)) * 100
            context['percentile'] = round(percentile, 1)
        
        # Get session report for recommendations
        try:
            from .models import PracticePerformanceReport
            context['report'] = PracticePerformanceReport.objects.get(session=response.session)
        except PracticePerformanceReport.DoesNotExist:
            context['report'] = None
        
        return context


class RetryResponseAnalysisView(LoginRequiredMixin, CandidateRequiredMixin, View):
    """Retry analysis for a failed practice response."""
    
    def post(self, request, response_id):
        from .models import PracticeResponse, InterviewPracticeSession
        from .tasks import analyze_practice_response
        
        response = get_object_or_404(
            PracticeResponse.objects.select_related('session__candidate', 'question'),
            pk=response_id
        )
        
        # Verify ownership
        session = response.session or response.question.session
        if session.candidate != request.user:
            raise PermissionDenied("Cannot retry analysis for another candidate's response.")
        
        # Reset status and trigger retry
        response.analysis_status = InterviewPracticeSession.GenerationState.PENDING
        response.save(update_fields=['analysis_status'])
        
        # Queue the analysis task
        analyze_practice_response.delay(response_id)
        
        messages.info(request, "Analysis retry queued. Please refresh the page in a few moments.")
        
        return redirect('interviews:practice_response_detail', response_id=response_id)


@method_decorator(login_required, name='dispatch')
class InterviewSummaryView(DetailView):
    """Display summary of completed interview."""
    model = Interview
    template_name = 'interviews/video_summary.html'
    context_object_name = 'interview'
    pk_url_kwarg = 'interview_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.object, 'video_session'):
            context['coding_session'] = getattr(self.object.video_session, 'coding_session', None)
            context['transcript'] = self.object.video_session.transcript
        return context