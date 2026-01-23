from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, FormView, TemplateView
)
from django.db.models import Q, Prefetch, Count, Avg
from django.db.models.functions import TruncWeek
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

from .models import Interview
from .forms import (
    InterviewScheduleForm, InterviewRescheduleForm, InterviewCancelForm,
    InterviewCompleteForm, InterviewNoShowForm, BulkInterviewActionForm,
    InterviewResponseForm
)
from .tasks import (
    send_interview_invitation,
    send_interview_cancellation,
    send_candidate_reschedule_request_email,
)
from apps.applications.models import Application, ApplicationStatus


class CompanyRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is a company account"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.account_type == 'company'
    
    def handle_no_permission(self):
        messages.error(self.request, "You need a company account to access this page.")
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
