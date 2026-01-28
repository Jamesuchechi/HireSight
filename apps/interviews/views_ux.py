"""
Views for interview practice UX improvements.
Handles session setup, warmup flow, progress tracking, and history dashboard.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Avg, Q, Count
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from .progress_tasks import generate_warmup_question_task

from .models import InterviewPracticeSession, PracticeQuestion, PracticeResponse


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
    """Display comprehensive practice history and statistics."""
    
    def get(self, request):
        """Show practice history dashboard."""
        user = request.user
        
        # Get all completed sessions
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        ).order_by('-completed_at')[:10]
        
        # Calculate statistics
        stats = self._calculate_stats(user, sessions)
        
        context = {
            'sessions': sessions,
            'stats': stats,
        }
        return render(request, 'interviews/practice/practice_history_dashboard.html', context)
    
    def _calculate_stats(self, user, sessions):
        """Calculate performance statistics for dashboard."""
        completed_sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        )
        
        # Basic stats
        all_sessions = list(completed_sessions)
        total_sessions = len(all_sessions)
        
        if not all_sessions:
            return {
                'total_sessions': 0,
                'average_score': 0,
                'score_trend': 0,
                'current_streak': 0,
                'next_goal': 80,
                'goal_progress': 0,
                'best_score': 0,
                'lowest_score': 0,
                'median_score': 0,
                'perfect_score': False,
                'categories_practiced': 0,
                'category_performance': []
            }
        
        # Calculate average score
        scores = [float(s.overall_score or 0) for s in all_sessions]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Calculate score trend (last week vs. average)
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        recent_sessions = [s for s in all_sessions if s.completed_at and s.completed_at >= week_ago]
        recent_avg = sum(float(s.overall_score or 0) for s in recent_sessions) / len(recent_sessions) if recent_sessions else avg_score
        score_trend = recent_avg - avg_score if avg_score > 0 else 0
        
        # Calculate streak
        streak = self._calculate_streak(user)
        
        # Category performance
        category_performance = self._calculate_category_performance(user)
        
        # Goal progress
        next_goal = 80
        goal_progress = min(int(avg_score), 100)
        
        # Other stats
        best_score = max(scores) if scores else 0
        lowest_score = min(scores) if scores else 0
        median_score = sorted(scores)[len(scores)//2] if scores else 0
        
        perfect_score = any(s >= 100 for s in scores)
        categories_practiced = len(category_performance)
        
        return {
            'total_sessions': total_sessions,
            'average_score': round(avg_score, 1),
            'score_trend': round(score_trend, 1),
            'current_streak': streak,
            'next_goal': next_goal,
            'goal_progress': goal_progress,
            'best_score': round(best_score, 1),
            'lowest_score': round(lowest_score, 1),
            'median_score': round(median_score, 1),
            'perfect_score': perfect_score,
            'categories_practiced': categories_practiced,
            'category_performance': category_performance
        }
    
    def _calculate_streak(self, user):
        """Calculate current practice streak (days in a row with practice)."""
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        ).order_by('-completed_at')
        
        streak = 0
        current_date = timezone.now().date()
        
        for session in sessions:
            if not session.completed_at:
                continue
                
            session_date = session.completed_at.date()
            
            if session_date == current_date or session_date == current_date - timedelta(days=1):
                if session_date != current_date:
                    current_date = session_date
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_category_performance(self, user):
        """Calculate average score by category."""
        sessions = InterviewPracticeSession.objects.filter(
            candidate=user,
            status=InterviewPracticeSession.Status.COMPLETED
        )
        
        category_scores = {}
        
        for session in sessions:
            responses = PracticeResponse.objects.filter(session=session)
            
            for response in responses:
                if not response.question:
                    continue
                    
                category = response.question.category or 'General'
                score = float(response.overall_score or 0)
                
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(score)
        
        # Calculate averages
        performance = []
        for category, scores in category_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            performance.append({
                'name': category.title(),
                'score': round(avg, 1)
            })
        
        return sorted(performance, key=lambda x: x['score'], reverse=True)


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
        PracticeResponse.objects.filter(
            session=session,
            question_id=question_id
        ).delete()
        
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