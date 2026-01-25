import json

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, View, FormView
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q, Prefetch, Count, Avg
from django.db.models.functions import TruncWeek
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid

from .models import (
    Interview, InterviewPracticeSession, PracticeQuestion,
    PracticeResponse, PracticePerformanceReport
)
from .forms import (
    InterviewScheduleForm, InterviewRescheduleForm, InterviewCancelForm,
    InterviewCompleteForm, InterviewNoShowForm, BulkInterviewActionForm,
    InterviewResponseForm, PracticeSessionForm, PracticeResponseForm
)
from .tasks import (
    send_interview_invitation,
    send_interview_cancellation,
    send_candidate_reschedule_request_email,
    generate_practice_questions,
    analyze_practice_response,
    generate_practice_report,
)
from apps.applications.models import Application, ApplicationStatus


class CompanyRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is a company account"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.account_type == 'company'
    
    def handle_no_permission(self):
        messages.error(self.request, "You need a company account to access this page.")
        return redirect('dashboard:dashboard_home')


class CandidateRequiredMixin(UserPassesTestMixin):
    """Ensure user is a personal account."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.account_type == 'personal'

    def handle_no_permission(self):
        messages.error(self.request, "Only personal accounts can access interview practice.")
        return redirect('dashboard:dashboard_home')


class InterviewAccessMixin:
    """Mixin to check if user has access to an interview"""
    
    def get_object(self, queryset=None):
        """Get interview and check permissions"""
        obj = super().get_object(queryset)
        
        # Company can access their own interviews
        if self.request.user.account_type == 'company':
            if obj.application.job.company.user != self.request.user:
                raise PermissionDenied("You don't have access to this interview.")
        
        # Candidate can access their own interviews
        elif self.request.user.account_type == 'personal':
            if obj.application.applicant != self.request.user:
                raise PermissionDenied("You don't have access to this interview.")
        
        return obj


class InterviewScheduleView(LoginRequiredMixin, CompanyRequiredMixin, CreateView):
    """
    Schedule a new interview for an application
    Only accessible by company users
    """
    model = Interview
    form_class = InterviewScheduleForm
    template_name = 'interviews/schedule_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Get and validate application"""
        self.application = get_object_or_404(
            Application.objects.select_related('job__company', 'applicant'),
            id=self.kwargs['application_id']
        )
        
        # Check if user owns this job posting
        if self.application.job.company.user != request.user:
            messages.error(request, "You don't have permission to schedule interviews for this application.")
            return redirect('applications:detail', pk=self.application.id)

        # Prevent duplicate interviews while an active slot exists
        now = timezone.now()
        existing_interview = Interview.objects.filter(
            application=self.application,
            status__in=[
                Interview.InterviewStatus.SCHEDULED,
                Interview.InterviewStatus.RESCHEDULED
            ],
            scheduled_date__gt=now
        ).order_by('scheduled_date').first()
        if existing_interview:
            messages.warning(
                request,
                "An interview is already scheduled for this application. "
                "Please reschedule or wait for the existing interview to complete before creating a new one."
            )
            return redirect('interviews:detail', interview_id=existing_interview.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add application to context"""
        context = super().get_context_data(**kwargs)
        context['application'] = self.application
        context['durations'] = [30, 45, 60, 90]
        return context
    
    def get_initial(self):
        """Pre-fill form with interviewer details"""
        initial = super().get_initial()
        company_profile = getattr(self.request.user, 'company_profile', None)
        interviewer_name = (
            getattr(company_profile, 'company_name', None)
            or self.request.user.get_display_name()
        )

        initial.update({
            'interviewer_name': interviewer_name,
            'interviewer_email': self.request.user.email,
        })
        return initial
    
    def form_valid(self, form):
        """Save interview and update application status"""
        form.instance.application = self.application
        form.instance.created_by = self.request.user
        
        response = super().form_valid(form)
        
        # Update application status to interview
        if self.application.status != ApplicationStatus.INTERVIEW:
            self.application.status = ApplicationStatus.INTERVIEW
            self.application.save(update_fields=['status'])
        
        # Send invitation email asynchronously
        send_interview_invitation.delay(self.object.id)
        
        messages.success(
            self.request,
            f"Interview scheduled successfully for {self.application.applicant.email}"
        )
        
        return response
    
    def get_success_url(self):
        """Redirect to the appropriate application detail view after scheduling."""
        if self.request.user.account_type == 'company':
            return reverse(
                'applications:applicant_detail',
                kwargs={'slug': self.application.job.slug, 'pk': self.application.id}
            )
        return reverse('applications:detail', kwargs={'pk': self.application.id})


class BulkInterviewScheduleView(LoginRequiredMixin, CompanyRequiredMixin, FormView):
    """Schedule interviews for multiple applications in one go."""
    template_name = 'interviews/bulk_schedule_form.html'
    form_class = InterviewScheduleForm

    def dispatch(self, request, *args, **kwargs):
        """Select applications owned by the company from query params."""
        app_ids = request.GET.getlist('applications')
        self.applications = Application.objects.filter(
            id__in=app_ids,
            job__company__user=request.user
        ).select_related('applicant', 'job')

        if not self.applications.exists():
            messages.error(request, "No valid applications selected for scheduling.")
            return redirect('applications:list')

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Create interviews for every selected application."""
        cleaned_data = form.cleaned_data.copy()
        created_count = 0

        for application in self.applications:
            interview = Interview(
                application=application,
                created_by=self.request.user,
                **cleaned_data
            )
            interview.save()
            send_interview_invitation.delay(interview.id)
            created_count += 1

        messages.success(
            self.request,
            f"Successfully scheduled {created_count} interviews."
        )
        return redirect('interviews:upcoming')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['applications'] = self.applications
        return context


class InterviewListView(LoginRequiredMixin, ListView):
    """
    List all interviews for the current user
    Shows different interviews based on account type
    """
    model = Interview
    template_name = 'interviews/interview_list.html'
    context_object_name = 'interviews'
    paginate_by = 20
    
    def get_queryset(self):
        """Get interviews based on user type and filters"""
        queryset = Interview.objects.all()

        # Filter by account type
        if self.request.user.account_type == 'company':
            queryset = queryset.for_company(self.request.user)
        else:
            queryset = queryset.for_candidate(self.request.user)

        queryset = queryset.select_related(
            'application__job__company',
            'application__applicant'
        ).prefetch_related(
            'application__job__company__user'
        )
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by time
        time_filter = self.request.GET.get('time')
        if time_filter == 'upcoming':
            queryset = queryset.upcoming()
        elif time_filter == 'past':
            queryset = queryset.past()
        
        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(application__job__title__icontains=search_query) |
                Q(application__applicant__email__icontains=search_query) |
                Q(interviewer_name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter options to context"""
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Interview.InterviewStatus.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['current_time'] = self.request.GET.get('time', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class UpcomingInterviewsView(LoginRequiredMixin, ListView):
    """
    Display upcoming interviews
    """
    model = Interview
    template_name = 'interviews/upcoming_list.html'
    context_object_name = 'interviews'
    paginate_by = 10
    
    def get_queryset(self):
        """Get upcoming interviews for current user"""
        queryset = Interview.objects.select_related(
            'application__job__company',
            'application__applicant'
        ).upcoming()
        
        if self.request.user.account_type == 'company':
            queryset = queryset.for_company(self.request.user)
        else:
            queryset = queryset.for_candidate(self.request.user)
        
        return queryset.order_by('scheduled_date')


class InterviewDetailView(LoginRequiredMixin, InterviewAccessMixin, DetailView):
    """
    Display detailed information about an interview
    """
    model = Interview
    template_name = 'interviews/interview_detail.html'
    context_object_name = 'interview'
    pk_url_kwarg = 'interview_id'
    
    def get_queryset(self):
        """Optimize query with related objects"""
        return Interview.objects.select_related(
            'application__job__company',
            'application__applicant',
            'created_by',
            'cancelled_by'
        )


class InterviewRescheduleView(LoginRequiredMixin, InterviewAccessMixin, FormView):
    """
    Reschedule an existing interview
    Accessible by both company and candidate
    """
    template_name = 'interviews/reschedule_form.html'
    form_class = InterviewRescheduleForm
    
    def dispatch(self, request, *args, **kwargs):
        """Get and validate interview"""
        self.interview = get_object_or_404(
            Interview.objects.select_related('application__job__company', 'application__applicant'),
            id=self.kwargs['interview_id']
        )
        
        # Check permissions
        is_company = request.user == self.interview.application.job.company.user
        is_candidate = request.user == self.interview.application.applicant
        
        if not (is_company or is_candidate):
            messages.error(request, "You don't have permission to reschedule this interview.")
            return redirect('interviews:upcoming')
        
        # Check if can be rescheduled
        if not self.interview.can_reschedule():
            messages.error(request, "This interview cannot be rescheduled.")
            return redirect('interviews:detail', interview_id=self.interview.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add interview to context"""
        context = super().get_context_data(**kwargs)
        context['interview'] = self.interview
        return context
    
    def form_valid(self, form):
        """Update interview with new schedule"""
        # Store original date if first reschedule
        if not self.interview.original_scheduled_date:
            self.interview.original_scheduled_date = self.interview.scheduled_date
        
        # Update interview
        self.interview.scheduled_date = form.cleaned_data['new_scheduled_date']
        self.interview.status = Interview.InterviewStatus.RESCHEDULED
        self.interview.reschedule_count += 1
        
        # Reset reminder flags
        self.interview.reminder_24h_sent = False
        self.interview.reminder_1h_sent = False
        
        # Add reschedule reason to notes
        reschedule_reason = form.cleaned_data['reschedule_reason']
        reschedule_note = f"\n[Rescheduled by {self.request.user.email} on {timezone.now():%Y-%m-%d %H:%M}]: {reschedule_reason}"
        self.interview.company_notes += reschedule_note
        
        self.interview.save()
        
        # Send notification
        send_interview_invitation.delay(self.interview.id, is_reschedule=True)
        
        messages.success(self.request, "Interview rescheduled successfully.")
        return redirect('interviews:detail', interview_id=self.interview.id)
    
    def get_success_url(self):
        return reverse('interviews:detail', kwargs={'interview_id': self.interview.id})

    def get_form_kwargs(self):
        """Pass interview instance to the form for validation"""
        kwargs = super().get_form_kwargs()
        kwargs['interview'] = self.interview
        return kwargs


class InterviewCancelView(LoginRequiredMixin, InterviewAccessMixin, FormView):
    """
    Cancel an interview
    Accessible by both company and candidate
    """
    template_name = 'interviews/cancel_form.html'
    form_class = InterviewCancelForm
    
    def dispatch(self, request, *args, **kwargs):
        """Get and validate interview"""
        self.interview = get_object_or_404(
            Interview.objects.select_related('application__job__company', 'application__applicant'),
            id=self.kwargs['interview_id']
        )
        
        # Check permissions
        is_company = request.user == self.interview.application.job.company.user
        is_candidate = request.user == self.interview.application.applicant
        
        if not (is_company or is_candidate):
            messages.error(request, "You don't have permission to cancel this interview.")
            return redirect('interviews:upcoming')
        
        # Check if can be cancelled
        if not self.interview.can_cancel():
            messages.error(request, "This interview cannot be cancelled.")
            return redirect('interviews:detail', interview_id=self.interview.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add interview to context"""
        context = super().get_context_data(**kwargs)
        context['interview'] = self.interview
        return context
    
    def form_valid(self, form):
        """Cancel the interview"""
        self.interview.status = Interview.InterviewStatus.CANCELLED
        self.interview.cancelled_by = self.request.user
        self.interview.cancellation_reason = form.cleaned_data['cancellation_reason']
        self.interview.cancelled_at = timezone.now()
        self.interview.save()
        
        # Send cancellation notification
        send_interview_cancellation.delay(self.interview.id)
        
        messages.success(self.request, "Interview cancelled successfully.")
        return redirect('interviews:upcoming')
    
    def get_success_url(self):
        return reverse('interviews:upcoming')


class InterviewCompleteView(LoginRequiredMixin, CompanyRequiredMixin, FormView):
    """
    Mark an interview as completed and add feedback
    Only accessible by company users
    """
    template_name = 'interviews/complete_form.html'
    form_class = InterviewCompleteForm
    
    def dispatch(self, request, *args, **kwargs):
        """Get and validate interview"""
        self.interview = get_object_or_404(
            Interview.objects.select_related('application__job__company', 'application__applicant'),
            id=self.kwargs['interview_id']
        )
        
        # Check if user owns this interview
        if self.interview.application.job.company.user != request.user:
            messages.error(request, "You don't have permission to complete this interview.")
            return redirect('interviews:upcoming')
        
        # Check if can be marked complete
        if not self.interview.can_mark_completed():
            messages.error(request, "This interview cannot be marked as completed yet.")
            return redirect('interviews:detail', interview_id=self.interview.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add interview to context"""
        context = super().get_context_data(**kwargs)
        context['interview'] = self.interview
        return context
    
    def form_valid(self, form):
        """Mark interview as completed"""
        self.interview.status = Interview.InterviewStatus.COMPLETED
        self.interview.completion_notes = form.cleaned_data['completion_notes']
        self.interview.interview_rating = form.cleaned_data.get('interview_rating')
        self.interview.interviewer_feedback = form.cleaned_data['interviewer_feedback']
        self.interview.feedback_template = form.cleaned_data.get('template')
        self.interview.save(update_fields=[
            'status',
            'completion_notes',
            'interview_rating',
            'interviewer_feedback',
            'feedback_template',
        ])
        
        messages.success(self.request, "Interview marked as completed.")
        return redirect('interviews:detail', interview_id=self.interview.id)
    
    def get_success_url(self):
        return reverse('interviews:detail', kwargs={'interview_id': self.interview.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company_user'] = self.request.user
        kwargs['interview_type'] = self.interview.interview_type
        return kwargs


class InterviewNoShowView(LoginRequiredMixin, CompanyRequiredMixin, FormView):
    """
    Mark a candidate as no-show
    Only accessible by company users
    """
    template_name = 'interviews/no_show_form.html'
    form_class = InterviewNoShowForm
    
    def dispatch(self, request, *args, **kwargs):
        """Get and validate interview"""
        self.interview = get_object_or_404(
            Interview.objects.select_related('application__job__company', 'application__applicant'),
            id=self.kwargs['interview_id']
        )
        
        # Check if user owns this interview
        if self.interview.application.job.company.user != request.user:
            messages.error(request, "You don't have permission to access this interview.")
            return redirect('interviews:upcoming')
        
        # Can only mark as no-show if interview time has passed
        if self.interview.scheduled_date > timezone.now():
            messages.error(request, "Cannot mark as no-show before interview time.")
            return redirect('interviews:detail', interview_id=self.interview.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add interview to context"""
        context = super().get_context_data(**kwargs)
        context['interview'] = self.interview
        return context
    
    def form_valid(self, form):
        """Mark as no-show"""
        self.interview.status = Interview.InterviewStatus.NO_SHOW
        self.interview.completion_notes = form.cleaned_data['no_show_notes']
        self.interview.no_show_contacted_candidate = form.cleaned_data['contacted_candidate']
        self.interview._activity_actor = self.request.user
        self.interview.save()
        
        messages.warning(self.request, "Candidate marked as no-show.")
        return redirect('interviews:detail', interview_id=self.interview.id)
    
    def get_success_url(self):
        return reverse('interviews:detail', kwargs={'interview_id': self.interview.id})


class InterviewCalendarExportView(LoginRequiredMixin, InterviewAccessMixin, DetailView):
    """
    Export interview to iCal format for calendar applications
    """
    model = Interview
    pk_url_kwarg = 'interview_id'
    
    def get(self, request, *args, **kwargs):
        """Generate and return .ics file"""
        interview = self.get_object()
        
        from .tasks import _build_ics
        ics_content = _build_ics(interview)
        
        response = HttpResponse(ics_content, content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="interview_{interview.id}.ics"'
        
        return response


class InterviewStatsView(LoginRequiredMixin, CompanyRequiredMixin, TemplateView):
    """
    Display interview statistics dashboard for company
    """
    template_name = 'interviews/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interviews = Interview.objects.for_company(self.request.user)

        stats = {
            'total_interviews': interviews.count(),
            'upcoming_interviews': interviews.upcoming().count(),
            'completed_interviews': interviews.filter(status=Interview.InterviewStatus.COMPLETED).count(),
            'cancelled_interviews': interviews.filter(status=Interview.InterviewStatus.CANCELLED).count(),
            'no_show_count': interviews.filter(status=Interview.InterviewStatus.NO_SHOW).count(),
            'avg_rating': interviews.filter(interview_rating__isnull=False).aggregate(Avg('interview_rating'))['interview_rating__avg'],
            'reschedule_rate': interviews.filter(reschedule_count__gt=0).count() / max(interviews.count(), 1) * 100,
        }

        type_map = dict(Interview.InterviewType.choices)
        stats['by_type'] = [
            {
                'interview_type': type_map.get(item['interview_type'], item['interview_type']),
                'count': item['count']
            }
            for item in interviews.values('interview_type').annotate(count=Count('id'))
        ]
        stats['recent_interviews'] = interviews.order_by('-scheduled_date')[:10]

        interviews_by_week = interviews.annotate(
            week=TruncWeek('scheduled_date')
        ).values('week').annotate(count=Count('id')).order_by('week')[:12]

        total_scheduled = stats['total_interviews']
        completed = stats['completed_interviews']
        high_rated = interviews.filter(interview_rating__gte=4).count()

        funnel = {
            'scheduled': total_scheduled,
            'completed': completed,
            'high_rated': high_rated,
            'completion_rate': (completed / max(total_scheduled, 1)) * 100,
            'success_rate': (high_rated / max(completed, 1)) * 100,
        }

        context.update({
            'stats': stats,
            'interviews_by_week': list(interviews_by_week),
            'funnel': funnel,
            'highlighted_stats': [
                {'key': 'total_interviews', 'label': 'Total Interviews', 'value': stats['total_interviews']},
                {'key': 'upcoming_interviews', 'label': 'Upcoming Interviews', 'value': stats['upcoming_interviews']},
                {'key': 'completed_interviews', 'label': 'Completed Interviews', 'value': stats['completed_interviews']},
                {'key': 'cancelled_interviews', 'label': 'Recent Cancellations', 'value': stats['cancelled_interviews']},
                {'key': 'no_show_count', 'label': 'No Shows', 'value': stats['no_show_count']},
                {'key': 'reschedule_rate', 'label': 'Reschedule Rate', 'value': stats['reschedule_rate'], 'suffix': '%'},
            ]
        })
        return context


class InterviewRespondView(LoginRequiredMixin, FormView):
    """
    Allow candidate to respond to an interview invitation
    """
    template_name = 'interviews/respond_form.html'
    form_class = InterviewResponseForm

    def dispatch(self, request, *args, **kwargs):
        """Ensure candidate owns invitation and it is pending"""
        self.interview = get_object_or_404(
            Interview.objects.select_related('application__applicant'),
            id=self.kwargs['interview_id']
        )

        if request.user != self.interview.application.applicant:
            raise PermissionDenied("Only the candidate can respond to this interview.")

        if self.interview.candidate_response != 'PENDING':
            messages.info(request, "You have already responded to this interview.")
            return redirect('interviews:detail', interview_id=self.interview.id)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['interview'] = self.interview
        return context

    def form_valid(self, form):
        action = form.cleaned_data['action']

        if action == 'accept':
            self.interview.candidate_response = 'ACCEPTED'
            self.interview.save(update_fields=['candidate_response'])
            messages.success(self.request, "Interview accepted!")

        elif action == 'decline':
            self.interview.candidate_response = 'DECLINED'
            self.interview.status = Interview.InterviewStatus.CANCELLED
            self.interview.cancellation_reason = form.cleaned_data.get('reason', 'Declined by candidate')
            self.interview.save(update_fields=['candidate_response', 'status', 'cancellation_reason'])
            messages.info(self.request, "Interview declined.")

        elif action == 'propose_reschedule':
            if not self.interview.can_reschedule():
                messages.error(self.request, "Cannot reschedule this interview.")
                return redirect('interviews:detail', interview_id=self.interview.id)

            self.interview.candidate_response = 'PROPOSED_RESCHEDULE'
            proposed_entry = {
                'date': form.cleaned_data['proposed_date'].isoformat(),
                'reason': form.cleaned_data['reason'],
                'proposed_at': timezone.now().isoformat(),
            }
            self.interview.proposed_times.append(proposed_entry)
            self.interview.save(update_fields=['candidate_response', 'proposed_times'])
            send_candidate_reschedule_request_email.delay(self.interview.id, proposed_entry)
            try:
                from apps.notifications.models import Notification

                Notification.objects.create(
                    user=self.interview.application.job.company.user,
                    notification_type='CANDIDATE_RESCHEDULE_REQUEST',
                    title='Candidate requested to reschedule',
                    message=(
                        f'{self.interview.application.applicant.email} requested a new time '
                        f'for {self.interview.application.job.title}.'
                    ),
                    action_url=f'/interviews/{self.interview.id}/'
                )
            except ImportError:
                pass
            messages.success(self.request, "Reschedule request sent to the company.")

        return redirect('interviews:detail', interview_id=self.interview.id)

    def get_success_url(self):
        return reverse('interviews:detail', kwargs={'interview_id': self.interview.id})


class PracticeSessionMixin(CandidateRequiredMixin):
    """Shared behavior for practice session views."""

    session_kwarg = 'session_id'

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            InterviewPracticeSession.objects.prefetch_related(
                'questions__responses'
            ).select_related('candidate', 'application__job'),
            pk=self.kwargs[self.session_kwarg]
        )
        if self.session.candidate != request.user:
            raise PermissionDenied("You can only view your own practice sessions.")
        self.session.next_question = self.session.questions.order_by('order').first()
        return super().dispatch(request, *args, **kwargs)


class PracticeDashboardView(LoginRequiredMixin, CandidateRequiredMixin, TemplateView):
    template_name = 'interviews/practice/practice_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sessions_qs = InterviewPracticeSession.objects.for_candidate(self.request.user).select_related('application__job').prefetch_related('questions')
        sessions = list(sessions_qs)
        for session in sessions:
            session.next_question = session.questions.order_by('order').first()
            session.has_report = hasattr(session, 'performance_report')
        context['sessions'] = sessions
        context['active_sessions'] = sum(
            1 for s in sessions if s.status in {
                InterviewPracticeSession.Status.CREATED,
                InterviewPracticeSession.Status.IN_PROGRESS,
                InterviewPracticeSession.Status.REVIEW_PENDING
            }
        )
        return context


class PracticeSessionCreateView(LoginRequiredMixin, CandidateRequiredMixin, CreateView):
    model = InterviewPracticeSession
    form_class = PracticeSessionForm
    template_name = 'interviews/practice/create_practice_session.html'

    def dispatch(self, request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        if not profile or not profile.practice_enabled:
            messages.error(request, "Practice sessions are currently disabled for your account.")
            return redirect('dashboard:dashboard_home')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['candidate'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.candidate = self.request.user
        response = super().form_valid(form)
        generate_practice_questions.delay(self.object.id)
        messages.success(self.request, "Practice session created. Questions are being generated now.")
        return response

    def get_success_url(self):
        return reverse('interviews:practice_dashboard')


class PracticeQuestionView(LoginRequiredMixin, CandidateRequiredMixin, FormView):
    template_name = 'interviews/practice/practice_question.html'
    form_class = PracticeResponseForm

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            PracticeQuestion.objects.select_related('session__candidate'),
            pk=self.kwargs['question_id']
        )
        if self.question.session.candidate != request.user:
            raise PermissionDenied("You can only answer your own practice questions.")
        self.session = self.question.session
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        context['session'] = self.session
        context['responses'] = self.question.responses.order_by('-submitted_at')
        return context

    def form_valid(self, form):
        response = PracticeResponse.objects.create(
            question=self.question,
            session=self.session,
            text_response=form.cleaned_data['text_response'],
            video_url=form.cleaned_data['video_url']
        )
        analyze_practice_response.delay(response.id)
        self.update_session_progress()
        messages.success(self.request, "Response submitted. AI scoring is in progress.")
        next_question = self.session.questions.filter(order__gt=self.question.order).order_by('order').first()
        if next_question:
            return redirect('interviews:practice_question', question_id=next_question.id)
        generate_practice_report.delay(self.session.id)
        return redirect('interviews:practice_feedback', session_id=self.session.id)

    def update_session_progress(self):
        total = self.session.questions.count()
        answered = PracticeResponse.objects.filter(session=self.session).values('question').distinct().count()
        progress = min(100, (answered / total) * 100) if total else 0
        self.session.progress = progress
        self.session.status = (
            InterviewPracticeSession.Status.REVIEW_PENDING
            if answered >= total and total > 0
            else InterviewPracticeSession.Status.IN_PROGRESS
        )
        self.session.save(update_fields=['progress', 'status'])


class PracticeFeedbackView(PracticeSessionMixin, TemplateView):
    template_name = 'interviews/practice/practice_feedback.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = self.session
        context['questions'] = self.session.questions.prefetch_related('responses')
        context['report'] = getattr(self.session, 'performance_report', None)
        responses = PracticeResponse.objects.filter(session=self.session, ai_score__isnull=False)
        context['best_responses'] = responses.order_by('-ai_score')[:2]
        context['worst_responses'] = responses.order_by('ai_score')[:2]
        return context


class PracticeReportView(PracticeSessionMixin, TemplateView):
    template_name = 'interviews/practice/practice_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = self.session
        context['report'] = getattr(self.session, 'performance_report', None)
        return context


@method_decorator(cache_page(60 * 15), name='dispatch')
class CachedPracticeReportView(PracticeReportView):
    """15-minute cached wrapper around practice report view."""
    pass


class PracticeReportRefreshView(PracticeSessionMixin, View):
    def post(self, request, *args, **kwargs):
        generate_practice_report.delay(self.session.id)
        messages.info(request, "Report refresh requested. Check back shortly.")
        return redirect('interviews:practice_report', session_id=self.session.id)


class PracticeResponseAnalysisView(LoginRequiredMixin, CandidateRequiredMixin, View):
    """Accept gaze/head metrics and detailed video analysis from the client and store them."""

    def post(self, request, response_id):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        response = get_object_or_404(
            PracticeResponse.objects.select_related('session__candidate', 'question__session__candidate'),
            pk=response_id
        )
        session = response.session or response.question.session
        if session.candidate != request.user:
            raise PermissionDenied("Cannot update another candidate's response.")

        # Update basic metrics
        response.gaze_direction = payload.get('gaze_direction', response.gaze_direction)
        response.head_tilt = payload.get('head_tilt', response.head_tilt)
        
        attention = payload.get('attention_score')
        if attention is not None:
            response.attention_score = attention
        
        analysis = payload.get('analysis')
        if analysis:
            response.analysis = analysis
        
        # Store detailed video analysis metrics if provided
        video_metrics = payload.get('video_analysis_metrics')
        if video_metrics:
            if not self._validate_metrics_structure(video_metrics):
                return JsonResponse({
                    'error': 'Invalid video_analysis_metrics structure'
                }, status=400)
            response.video_analysis_metrics = video_metrics
        
        response.save(update_fields=[
            'gaze_direction',
            'head_tilt',
            'attention_score',
            'analysis',
            'video_analysis_metrics'
        ])
        
        return JsonResponse({
            'status': 'updated',
            'message': 'Response and video analysis metrics updated successfully',
            'response_id': str(response_id)
        })
    
    @staticmethod
    def _validate_metrics_structure(metrics):
        """
        Validate that the video_analysis_metrics have the expected structure.
        
        Expected structure:
        {
            "summary": {
                "totalDuration": float,
                "averageGazeAtCamera": float,
                "averageBlinkRate": float,
                "averageEyeOpenPercentage": float,
                "speakingPercentage": float,
                "averageHeadPose": {"pitch": float, "yaw": float, "roll": float},
                "metricsCount": int
            },
            "detailed_metrics": [
                {
                    "timestamp": int,
                    "secondsElapsed": float,
                    "eyeOpenPercentage": float,
                    "mouthOpenPercentage": float,
                    "blinkRatePerMinute": float,
                    "gazeAtCameraPercent": float,
                    "headPose": {"pitch": float, "yaw": float, "roll": float},
                    "speakingDetected": bool
                }
            ]
        }
        """
        if not isinstance(metrics, dict):
            return False
        
        # Validate summary section
        summary = metrics.get('summary')
        if not summary or not isinstance(summary, dict):
            return False
        
        required_summary_fields = [
            'totalDuration',
            'averageGazeAtCamera',
            'averageBlinkRate',
            'averageEyeOpenPercentage',
            'speakingPercentage',
            'averageHeadPose',
            'metricsCount'
        ]
        
        for field in required_summary_fields:
            if field not in summary:
                return False
        
        # Validate head pose in summary
        head_pose = summary.get('averageHeadPose')
        if not isinstance(head_pose, dict):
            return False
        
        for pose_field in ['pitch', 'yaw', 'roll']:
            if pose_field not in head_pose:
                return False
        
        # Validate detailed metrics if present
        detailed = metrics.get('detailed_metrics', [])
        if not isinstance(detailed, list):
            return False
        
        for metric in detailed:
            if not isinstance(metric, dict):
                return False
            
            required_fields = [
                'timestamp',
                'secondsElapsed',
                'eyeOpenPercentage',
                'mouthOpenPercentage',
                'blinkRatePerMinute',
                'gazeAtCameraPercent',
                'headPose',
                'speakingDetected'
            ]
            
            for field in required_fields:
                if field not in metric:
                    return False
            
            # Validate head pose in each metric
            pose = metric.get('headPose')
            if not isinstance(pose, dict):
                return False
            
            for pose_field in ['pitch', 'yaw', 'roll']:
                if pose_field not in pose:
                    return False
        
        return True


class PracticeVideoUploadView(LoginRequiredMixin, CandidateRequiredMixin, View):
    """Accept chunked uploads for practice response videos, assemble and return final URL."""

    def post(self, request, *args, **kwargs):
        upload_id = request.POST.get('upload_id') or str(uuid.uuid4())
        session_id = request.POST.get('session_id')
        question_id = request.POST.get('question_id')
        chunk_index = int(request.POST.get('chunk_index', 0))
        total_chunks = int(request.POST.get('total_chunks', 1))
        filename = request.POST.get('filename', 'upload.webm')

        if 'chunk' not in request.FILES:
            return JsonResponse({'error': 'No chunk provided'}, status=400)

        # Save chunk to temporary upload dir
        tmp_dir = os.path.join(getattr(settings, 'MEDIA_ROOT', 'media'), 'practice_uploads', upload_id)
        os.makedirs(tmp_dir, exist_ok=True)
        chunk_path = os.path.join(tmp_dir, f'chunk_{chunk_index:05d}')

        with open(chunk_path, 'wb') as fh:
            for chunk in request.FILES['chunk'].chunks():
                fh.write(chunk)

        # If last chunk, assemble
        assembled_url = None
        if chunk_index + 1 >= total_chunks:
            # Assemble
            assembled_bytes = bytearray()
            for i in range(total_chunks):
                part = os.path.join(tmp_dir, f'chunk_{i:05d}')
                with open(part, 'rb') as pf:
                    assembled_bytes.extend(pf.read())

            final_name = f'practice_videos/{uuid.uuid4().hex}_{filename}'
            saved_path = default_storage.save(final_name, ContentFile(bytes(assembled_bytes)))
            assembled_url = default_storage.url(saved_path)

            # Cleanup tmp
            try:
                for f in os.listdir(tmp_dir):
                    os.remove(os.path.join(tmp_dir, f))
                os.rmdir(tmp_dir)
            except Exception:
                pass

            # Optionally schedule thumbnail generation (task exists in tasks.py?)
            try:
                from .tasks import generate_video_thumbnail
                generate_video_thumbnail.delay(saved_path)
            except Exception:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(Exception('Failed to schedule thumbnail task'))
                except Exception:
                    pass

            # Create a PracticeResponse record linking to the question/session
            try:
                session = None
                question = None
                if question_id:
                    question = PracticeQuestion.objects.select_related('session__candidate').get(pk=question_id)
                    session = question.session
                elif session_id:
                    session = InterviewPracticeSession.objects.select_related('candidate').get(pk=session_id)

                # Ensure ownership
                if session and session.candidate != request.user:
                    return JsonResponse({'error': 'Permission denied for this session'}, status=403)

                if session:
                    response = PracticeResponse.objects.create(
                        question=question,
                        session=session,
                        text_response='',
                        video_url=assembled_url
                    )

                    # Kick off scoring/analysis for this response
                    try:
                        analyze_practice_response.delay(response.id)
                    except Exception:
                        pass

                    # Update session progress
                    try:
                        total = session.questions.count()
                        answered = PracticeResponse.objects.filter(session=session).values('question').distinct().count()
                        progress = min(100, (answered / total) * 100) if total else 0
                        session.progress = progress
                        session.status = (
                            InterviewPracticeSession.Status.REVIEW_PENDING
                            if answered >= total and total > 0
                            else InterviewPracticeSession.Status.IN_PROGRESS
                        )
                        session.save(update_fields=['progress', 'status'])

                        # If all responses analyzed, schedule report generation (task will check)
                        generate_practice_report.delay(session.id)
                    except Exception:
                        pass

                    return JsonResponse({'upload_id': upload_id, 'video_url': assembled_url, 'response_id': response.id})
            except PracticeQuestion.DoesNotExist as e:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(e)
                except Exception:
                    pass
                return JsonResponse({'error': 'Question not found'}, status=404)
            except InterviewPracticeSession.DoesNotExist as e:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(e)
                except Exception:
                    pass
                return JsonResponse({'error': 'Session not found'}, status=404)

        return JsonResponse({'upload_id': upload_id, 'video_url': assembled_url})
