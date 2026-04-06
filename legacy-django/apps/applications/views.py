"""
Application views for job applications.
"""
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import (
    CreateView, ListView, DetailView, UpdateView, DeleteView, FormView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.db.models import Q, Avg, Count, Prefetch, ExpressionWrapper, DurationField, F
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.utils.timezone import now, timedelta, datetime
from .models import (
    Application,
    ApplicationNote,
    ApplicationStatusHistory,
    ApplicationStatus
)
from .forms import (
    ApplicationForm, ApplicationReviewForm, ApplicationFilterForm,
    ApplicationBulkActionForm, ApplicationNoteForm, ApplicationWithdrawForm,
    ApplicationRejectionForm
)
from .validators import validate_application_ownership
from apps.jobs.models import Job
from apps.resumes.models import Resume
from django.utils.decorators import method_decorator
from .decorators import personal_account_required, company_account_required
from apps.resumes.views import ResumeDownloadView as BaseResumeDownloadView, ResumePreviewView as BaseResumePreviewView
from .utils import build_pipeline_data


# Set up logging
logger = logging.getLogger(__name__)

def build_pipeline_stats(queryset):
    """Return pipeline stats for statuses and average match score."""
    totals = {status.value: queryset.filter(status=status.value).count() for status in ApplicationStatus}
    stats = {
        'total': queryset.count(),
        'pending': totals.get(ApplicationStatus.PENDING.value, 0),
        'screening': totals.get(ApplicationStatus.SCREENING.value, 0),
        'interview': totals.get(ApplicationStatus.INTERVIEW.value, 0),
        'offer': totals.get(ApplicationStatus.OFFER.value, 0),
        'hired': totals.get(ApplicationStatus.HIRED.value, 0),
        'rejected': totals.get(ApplicationStatus.REJECTED.value, 0),
        'shortlisted': queryset.filter(is_shortlisted=True).count(),
        'avg_match_score': queryset.exclude(match_score__isnull=True).aggregate(avg=Avg('match_score'))['avg'] or 0,
    }
    return stats


def build_stage_summary(queryset):
    """Build stage summary data with conversion percentages and average time."""
    total_applications = queryset.count()
    now = timezone.now()
    stage_summary = []

    for status in ApplicationStatus:
        stage_qs = queryset.filter(status=status.value)
        count = stage_qs.count()
        percent = round((count / total_applications) * 100, 1) if total_applications else 0
        duration_expr = ExpressionWrapper(now - F('status_changed_at'), output_field=DurationField())
        avg_duration = stage_qs.aggregate(avg_time=Avg(duration_expr))['avg_time']
        avg_days = round(avg_duration.total_seconds() / 86400, 1) if avg_duration else 0
        stage_summary.append({
            'label': status.label,
            'value': status.value,
            'count': count,
            'percent': percent,
            'avg_days': avg_days,
        })

    return stage_summary


def build_history_summary(queryset, days=7):
    """Return conversion counts for the last N days per status."""
    cutoff = timezone.now() - timedelta(days=days)
    prev_cutoff = cutoff - timedelta(days=days)
    application_ids = list(queryset.values_list('id', flat=True))

    recent_history = ApplicationStatusHistory.objects.filter(
        application_id__in=application_ids,
        changed_at__gte=cutoff
    ).values('new_status').annotate(count=Count('id'))

    previous_history = ApplicationStatusHistory.objects.filter(
        application_id__in=application_ids,
        changed_at__gte=prev_cutoff,
        changed_at__lt=cutoff
    ).values('new_status').annotate(count=Count('id'))

    previous_map = {item['new_status']: item['count'] for item in previous_history}
    history_summary = []

    for status in ApplicationStatus:
        current_count = next((item['count'] for item in recent_history if item['new_status'] == status.value), 0)
        prev_count = previous_map.get(status.value, 0)
        change = None
        if prev_count:
            change = round(((current_count - prev_count) / prev_count) * 100, 1)

        history_summary.append({
            'label': status.label,
            'value': status.value,
            'count': current_count,
            'change': change,
        })

    return history_summary


def build_pipeline_data(queryset):
    """Aggregate pipeline stats, stage summary, and history data."""
    return {
        'stats': build_pipeline_stats(queryset),
        'stage_summary': build_stage_summary(queryset),
        'history_summary': build_history_summary(queryset),
    }


class ApplicationOwnerMixin:
    """Mixin to ensure only the applicant can access their applications."""

    def get_queryset(self):
        queryset = super().get_queryset()
        # ✅ Add query optimization
        queryset = queryset.select_related(
            'job',
            'job__company',
            'job__company__user',
            'applicant',
            'applicant__personal_profile',
            'resume'
        ).prefetch_related(
            Prefetch('status_history', queryset=ApplicationStatusHistory.objects.select_related('changed_by')),
            Prefetch('notes', queryset=ApplicationNote.objects.select_related('author'))
        )
        return queryset.filter(applicant=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        validate_application_ownership(obj, self.request.user)
        return obj


class JobOwnerMixin:
    """Mixin to ensure only the job owner can access applicants."""

    def get_queryset(self):
        queryset = super().get_queryset()
        # ✅ Add query optimization
        queryset = queryset.select_related(
            'job',
            'job__company',
            'job__company__user',
            'applicant',
            'applicant__personal_profile',
            'resume'
        ).prefetch_related(
            Prefetch('status_history', queryset=ApplicationStatusHistory.objects.select_related('changed_by')),
            Prefetch('notes', queryset=ApplicationNote.objects.select_related('author'))
        )
        # Only show applications for jobs owned by the user's company
        return queryset.filter(job__company__user=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.job.company.user != self.request.user:
            logger.warning(f"Unauthorized access attempt to application {obj.id} by user {self.request.user.id}")
            raise PermissionDenied("You can only access applications for your company's jobs.")
        return obj


class PreventDuplicateApplicationMixin:
    """Mixin to prevent duplicate applications."""

    # ✅ FIXED: Moved from get_initial() to dispatch()
    def dispatch(self, request, *args, **kwargs):
        """Check for duplicate application before processing request."""
        job = self.get_job()
        
        # Check if user has already applied
        has_applied = Application.objects.filter(
            job=job,
            applicant=request.user
        ).exists()
        
        if has_applied:
            messages.warning(request, "You have already applied to this job.")
            logger.info(f"Duplicate application attempt for job {job.id} by user {request.user.id}")
            return redirect('jobs:detail', slug=job.slug)
        
        return super().dispatch(request, *args, **kwargs)

    def get_job(self):
        """Get the job object."""
        job_slug = self.kwargs.get('slug')
        return get_object_or_404(Job, slug=job_slug)


# ===========================
# Job Seeker Views
# ===========================

class JobApplyView(LoginRequiredMixin, PreventDuplicateApplicationMixin, CreateView):
    """View for job seekers to apply to a job."""

    model = Application
    form_class = ApplicationForm
    template_name = 'applications/application_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['job'] = self.get_job()
        kwargs['applicant'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_job()
        context['job'] = job
        
        # Get applicant's resumes with optimization
        context['resumes'] = self.request.user.resumes.all()
        
        # Check if user has primary resume
        primary_resume = self.request.user.resumes.filter(is_primary=True).first()
        if primary_resume:
            context['primary_resume'] = primary_resume
            context['primary_resume_auto_select'] = True
            context['primary_resume_url'] = primary_resume.file.url if getattr(primary_resume, 'file', None) else None
        
        return context

    @transaction.atomic  # ✅ Add transaction handling
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            response = super().form_valid(form)
            
            # Increment job application count
            job = self.get_job()
            job.increment_applications()
            
            # Log successful application
            logger.info(f"Application created: {self.object.id} for job {job.id} by user {self.request.user.id}")
            
            messages.success(self.request, "Your application has been submitted successfully!")
            
            # Trigger async tasks
            from .tasks import send_application_confirmation_email, calculate_application_match_score
            send_application_confirmation_email.delay(self.object.id)
            
            # Queue match score calculation if resume is attached
            if self.object.resume:
                calculate_application_match_score.delay(self.object.id)
            
            return response
        except Exception as e:
            logger.error(f"Error creating application: {str(e)}", exc_info=True)
            messages.error(self.request, "An error occurred while submitting your application. Please try again.")
            return self.form_invalid(form)

    def get_success_url(self):
        """Redirect to application detail or job detail."""
        return reverse('applications:detail', kwargs={'pk': self.object.pk})


@method_decorator(personal_account_required, name='dispatch')
class ApplicationListView(LoginRequiredMixin, ApplicationOwnerMixin, ListView):
    """View for job seekers to see all their applications."""

    model = Application
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filtering
        status = self.request.GET.get('status')
        search_query = self.request.GET.get('search')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if search_query:
            queryset = queryset.filter(
                Q(job__title__icontains=search_query) |
                Q(job__company__company_name__icontains=search_query)
            )
        
        if date_from:
            queryset = queryset.filter(applied_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(applied_at__lte=date_to)
        
        return queryset.order_by('-applied_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ApplicationFilterForm(self.request.GET)
        context['status_choices'] = ApplicationStatus.choices
        
        # Add statistics
        applications = self.get_queryset()
        context['stats'] = {
            'total': applications.count(),
            'active': applications.filter(status__in=[
                ApplicationStatus.PENDING,
                ApplicationStatus.SCREENING,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFER
            ]).count(),
            'pending': applications.filter(status=ApplicationStatus.PENDING).count(),
            'interview': applications.filter(status=ApplicationStatus.INTERVIEW).count(),
        }
        
        return context


class ApplicationDetailView(LoginRequiredMixin, ApplicationOwnerMixin, DetailView):
    """View for job seekers to see details of a single application."""

    model = Application
    template_name = 'applications/personal_application_detail.html'
    context_object_name = 'application'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.object
        
        # Add status history
        context['status_history'] = application.status_history.all()
        
        # Add notes (if visible to applicant)
        context['notes'] = application.notes.filter(is_important=True)  # Only show important notes
        
        # Add withdrawal form if eligible
        if application.can_withdraw:
            context['withdraw_form'] = ApplicationWithdrawForm()
        
        # Add timeline data
        context['timeline'] = self._build_timeline(application)
        
        return context
    
    def _build_timeline(self, application):
        """Build application timeline."""
        timeline = []
        
        # Application submitted
        timeline.append({
            'date': application.applied_at,
            'event': 'Application Submitted',
            'description': f'Applied for {application.job.title}',
            'icon': 'check-circle'
        })
        
        # Status changes
        for history in application.status_history.all():
            timeline.append({
                'date': history.changed_at,
                'event': f'Status: {history.get_new_status_display()}',
                'description': history.notes or '',
                'icon': 'arrow-right'
            })
        
        return sorted(timeline, key=lambda x: x['date'], reverse=True)


class ApplicationWithdrawView(LoginRequiredMixin, ApplicationOwnerMixin, FormView):
    """View for job seekers to withdraw their application."""

    form_class = ApplicationWithdrawForm
    template_name = 'applications/withdraw_confirm.html'

    def get_application(self):
        """Get application object."""
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            Application.objects.select_related('job', 'applicant'),
            pk=pk,
            applicant=self.request.user
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['application'] = self.get_application()
        return kwargs

    @transaction.atomic  # ✅ Add transaction handling
    def form_valid(self, form):
        """Handle valid withdrawal form."""
        try:
            application = form.save()
            
            logger.info(f"Application withdrawn: {application.id} by user {self.request.user.id}")
            messages.success(self.request, "Your application has been withdrawn successfully.")
            
            # Trigger async task to send email
            from .tasks import send_withdrawal_notification_email
            send_withdrawal_notification_email.delay(application.id)
            
            return redirect('applications:my_applications')
        except Exception as e:
            logger.error(f"Error withdrawing application: {str(e)}", exc_info=True)
            messages.error(self.request, "An error occurred while withdrawing your application.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = self.get_application()
        return context


# ===========================
# Company Views
# ===========================

@method_decorator(company_account_required, name='dispatch')
class ApplicationManageView(LoginRequiredMixin, JobOwnerMixin, ListView):
    """View for companies to manage all applicants for their jobs."""

    model = Application
    template_name = 'applications/job_applicants.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect personal accounts away from company views
        if request.user.account_type == 'personal':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('applications:my_applications')
        return super().dispatch(request, *args, **kwargs)
    
    def get_template_names(self):
        # Choose template based on URL pattern
        if 'slug' in self.kwargs:
            # Job-specific pipeline view
            return ['applications/application_pipeline.html']
        else:
            # All applications view
            return ['applications/applicant_list.html']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by job if specified
        job_slug = self.kwargs.get('slug')
        if job_slug:
            job = get_object_or_404(Job, slug=job_slug, company__user=self.request.user)
            queryset = queryset.filter(job=job)
        
        # Apply filtering
        filter_form = ApplicationFilterForm(self.request.GET)
        if filter_form.is_valid():
            status = filter_form.cleaned_data.get('status')
            min_score = filter_form.cleaned_data.get('match_score_min')
            max_score = filter_form.cleaned_data.get('match_score_max')
            rating = filter_form.cleaned_data.get('rating')
            is_shortlisted = filter_form.cleaned_data.get('is_shortlisted')
            search_query = filter_form.cleaned_data.get('search_query')
            date_from = filter_form.cleaned_data.get('date_from')
            date_to = filter_form.cleaned_data.get('date_to')
            
            if status:
                queryset = queryset.filter(status=status)
            
            if min_score is not None:
                queryset = queryset.filter(match_score__gte=min_score)
            
            if max_score is not None:
                queryset = queryset.filter(match_score__lte=max_score)
            
            if rating:
                queryset = queryset.filter(rating__gte=int(rating))
            
            if is_shortlisted:
                queryset = queryset.filter(is_shortlisted=True)
            
            if search_query:
                queryset = queryset.filter(
                    Q(applicant__personal_profile__full_name__icontains=search_query) |
                    Q(applicant__email__icontains=search_query)
                )
            
            if date_from:
                queryset = queryset.filter(applied_at__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(applied_at__lte=date_to)
        
        return queryset.order_by('-last_activity_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form
        context['filter_form'] = ApplicationFilterForm(self.request.GET)
        
        # Add bulk action form
        context['bulk_action_form'] = ApplicationBulkActionForm()
        
        # Add job information if filtering by job
        job_slug = self.kwargs.get('slug')
        if job_slug:
            context['job'] = get_object_or_404(Job, slug=job_slug)
        
        queryset = self.get_queryset()
        pipeline_data = build_pipeline_data(queryset)
        context['stats'] = pipeline_data['stats']
        context['stage_summary'] = pipeline_data['stage_summary']
        context['history_summary'] = pipeline_data['history_summary']
        
        return context


class ApplicantDetailView(LoginRequiredMixin, JobOwnerMixin, DetailView):
    """View for companies to see detailed applicant profile."""

    model = Application
    template_name = 'applications/company_applicant_detail.html'
    context_object_name = 'application'

    def get_object(self, queryset=None):
        """Get object and mark as viewed."""
        obj = super().get_object(queryset)
        
        # Mark as viewed if not already viewed
        if not obj.viewed_at:
            obj.mark_as_viewed()
            logger.info(f"Application {obj.id} marked as viewed by user {self.request.user.id}")
        
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.object
        
        # Add job to context for template URL generation
        context['job'] = application.job
        
        # Add status history
        context['status_history'] = application.status_history.all()
        
        # Add notes
        context['notes'] = application.notes.all()
        
        # Add review form
        context['review_form'] = ApplicationReviewForm(instance=application)
        
        # Add note form
        context['note_form'] = ApplicationNoteForm()
        
        # Add applicant profile
        context['profile'] = application.applicant.personal_profile
        
        # Add resume data
        if application.resume:
            context['resume'] = application.resume
        
        return context


class ApplicationUpdateStatusView(LoginRequiredMixin, JobOwnerMixin, UpdateView):
    """View for companies to update application status."""

    model = Application
    form_class = ApplicationReviewForm
    template_name = 'applications/update_status.html'
    context_object_name = 'application'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    @transaction.atomic  # ✅ Add transaction handling
    def form_valid(self, form):
        """Handle valid status update."""
        try:
            # Check if status is being changed to rejected
            if form.cleaned_data.get('status') == ApplicationStatus.REJECTED:
                # Redirect to rejection feedback form
                return redirect('applications:reject_application', pk=self.get_object().pk)

            response = super().form_valid(form)
            
            logger.info(f"Application {self.object.id} status updated by user {self.request.user.id}")
            messages.success(self.request, "Application status updated successfully.")
            
            # Trigger async task to send email
            from .tasks import send_status_update_email
            send_status_update_email.delay(self.object.id)
            
            return response
        except Exception as e:
            logger.error(f"Error updating application status: {str(e)}", exc_info=True)
            messages.error(self.request, "An error occurred while updating the application.")
            return self.form_invalid(form)

    def get_success_url(self):
        """Redirect back to applicant detail."""
        return reverse(
            'applications:applicant_detail',
            kwargs={'slug': self.object.job.slug, 'pk': self.object.pk}
        )


class ApplicationRejectView(LoginRequiredMixin, JobOwnerMixin, FormView):
    """View for companies to reject applications with feedback."""

    form_class = ApplicationRejectionForm
    template_name = 'applications/reject_application.html'

    def get_application(self):
        """Get application object."""
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            Application.objects.select_related('job', 'applicant'),
            pk=pk,
            job__company__user=self.request.user
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['application'] = self.get_application()
        return kwargs

    @transaction.atomic  # ✅ Add transaction handling
    def form_valid(self, form):
        """Handle valid rejection form."""
        try:
            application = form.save()

            # Send rejection email if requested
            if form.cleaned_data.get('notify_applicant', True):
                from .tasks import send_status_update_email
                send_status_update_email.delay(application.id)

            logger.info(f"Application {application.id} rejected by user {self.request.user.id}")
            messages.success(self.request, "Application rejected successfully.")

            return redirect('applications:applicant_detail', pk=application.pk)
        except Exception as e:
            logger.error(f"Error rejecting application: {str(e)}", exc_info=True)
            messages.error(self.request, "An error occurred while rejecting the application.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = self.get_application()
        return context


class ApplicationBulkActionView(LoginRequiredMixin, FormView):
    """View for companies to perform bulk actions on applications."""

    form_class = ApplicationBulkActionForm
    template_name = 'applications/bulk_action.html'

    @transaction.atomic  # ✅ Add transaction handling
    def form_valid(self, form):
        """Handle valid bulk action."""
        application_ids = self.request.POST.getlist('application_ids')
        applications = Application.objects.filter(
            id__in=application_ids,
            job__company__user=self.request.user  # ✅ Verify ownership
        ).select_related('job', 'applicant')
        
        action = form.cleaned_data['action']
        
        success_count = 0
        error_count = 0
        
        try:
            for application in applications:
                try:
                    if action == 'shortlist':
                        application.is_shortlisted = True
                        application.save(update_fields=['is_shortlisted'])
                        success_count += 1
                    
                    elif action == 'unshortlist':
                        application.is_shortlisted = False
                        application.save(update_fields=['is_shortlisted'])
                        success_count += 1
                    
                    elif action == 'status':
                        new_status = form.cleaned_data['new_status']
                        application.update_status(new_status, self.request.user)
                        success_count += 1
                    
                    elif action == 'rating':
                        rating = int(form.cleaned_data['rating'])
                        application.rating = rating
                        application.save(update_fields=['rating'])
                        success_count += 1
                    
                    elif action == 'tag':
                        tag = form.cleaned_data['tag']
                        if tag not in application.tags:
                            application.tags.append(tag)
                            application.save(update_fields=['tags'])
                        success_count += 1
                    
                    elif action == 'remove_tag':
                        tag = form.cleaned_data['tag']
                        if tag in application.tags:
                            application.tags.remove(tag)
                            application.save(update_fields=['tags'])
                        success_count += 1
                    
                    elif action == 'delete':
                        application.delete()
                        success_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing application {application.id}: {str(e)}", exc_info=True)
            
            if success_count > 0:
                messages.success(self.request, f"Successfully processed {success_count} applications.")
                logger.info(f"Bulk action '{action}' completed: {success_count} successful, {error_count} failed")
            
            if error_count > 0:
                messages.warning(self.request, f"Failed to process {error_count} applications.")
            
        except Exception as e:
            logger.error(f"Error in bulk action: {str(e)}", exc_info=True)
            messages.error(self.request, "An error occurred while processing bulk action.")
        
        return redirect('applications:manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get selected applications
        application_ids = self.request.POST.getlist('application_ids')
        context['applications'] = Application.objects.filter(
            id__in=application_ids
        ).select_related('job', 'applicant')
        
        return context


class ApplicationRatingView(LoginRequiredMixin, JobOwnerMixin, View):
    """Quick rating endpoint for applications."""

    def get_application(self):
        """Retrieve application ensuring the company owns it."""
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            Application.objects.select_related('job', 'job__company'),
            pk=pk,
            job__company__user=self.request.user
        )

    def post(self, request, *args, **kwargs):
        application = self.get_application()
        try:
            rating = int(request.POST.get('rating', ''))
        except (TypeError, ValueError):
            messages.error(request, "Please provide a valid rating between 1 and 5.")
            return redirect('applications:applicant_detail', slug=application.job.slug, pk=application.pk)

        if rating < 1 or rating > 5:
            messages.error(request, "Rating must be between 1 and 5 stars.")
            return redirect('applications:applicant_detail', slug=application.job.slug, pk=application.pk)

        application.rating = rating
        application.save(update_fields=['rating'])
        messages.success(request, "Candidate rating updated.")
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('applications:applicant_detail', slug=application.job.slug, pk=application.pk)


class ApplicationTagView(LoginRequiredMixin, View):
    """Quick endpoint for adding tags to an application."""

    def get_application(self):
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            Application.objects.select_related('job', 'job__company').prefetch_related('job__company__user'),
            pk=pk
        )

    def post(self, request, *args, **kwargs):
        application = self.get_application()
        if application.job.company.user != request.user:
            logger.warning(f"Unauthorized tag attempt on application {application.id} by user {request.user.id}")
            raise PermissionDenied("You can only tag applications for your company.")

        tag_value = (request.POST.get('tag') or '').strip()
        if not tag_value:
            messages.error(request, "Please provide a tag name.")
            return redirect('applications:applicant_detail', slug=application.job.slug, pk=application.pk)

        tags = list(application.tags or [])
        if tag_value in tags:
            messages.info(request, f"Tag '{tag_value}' is already added.")
        else:
            tags.append(tag_value)
            application.tags = tags
            application.save(update_fields=['tags'])
            messages.success(request, f"Added tag '{tag_value}'.")

        return redirect('applications:applicant_detail', slug=application.job.slug, pk=application.pk)


class ApplicationNoteCreateView(LoginRequiredMixin, CreateView):
    """View for companies to add notes to applications."""

    model = ApplicationNote
    form_class = ApplicationNoteForm
    template_name = 'applications/add_note.html'

    def get_application(self):
        """Get the application object."""
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            Application.objects.select_related('job', 'job__company'),
            pk=pk,
            job__company__user=self.request.user
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['application'] = self.get_application()
        kwargs['author'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = self.get_application()
        return context

    @transaction.atomic  # ✅ Add transaction handling
    def form_valid(self, form):
        """Handle valid note creation."""
        try:
            response = super().form_valid(form)
            
            logger.info(f"Note added to application {self.get_application().id} by user {self.request.user.id}")
            messages.success(self.request, "Note added successfully.")
            
            return response
        except Exception as e:
            logger.error(f"Error adding note: {str(e)}", exc_info=True)
            messages.error(self.request, "An error occurred while adding the note.")
            return self.form_invalid(form)

    def get_success_url(self):
        """Redirect back to applicant detail."""
        application = self.get_application()
        return reverse(
            'applications:applicant_detail',
            kwargs={'slug': application.job.slug, 'pk': application.pk}
        )


class ApplicationExportView(LoginRequiredMixin, View):
    """View for companies to export application data."""

    def get(self, request, *args, **kwargs):
        """Handle export request."""
        import csv
        from io import StringIO
        
        try:
            # Get applications based on filters
            queryset = Application.objects.filter(
                job__company__user=request.user
            ).select_related('job', 'applicant', 'applicant__personal_profile')
            
            # Apply same filtering as manage view
            filter_form = ApplicationFilterForm(request.GET)
            if filter_form.is_valid():
                status = filter_form.cleaned_data.get('status')
                min_score = filter_form.cleaned_data.get('match_score_min')
                max_score = filter_form.cleaned_data.get('match_score_max')
                is_shortlisted = filter_form.cleaned_data.get('is_shortlisted')
                
                if status:
                    queryset = queryset.filter(status=status)
                
                if min_score is not None:
                    queryset = queryset.filter(match_score__gte=min_score)
                
                if max_score is not None:
                    queryset = queryset.filter(match_score__lte=max_score)
                
                if is_shortlisted:
                    queryset = queryset.filter(is_shortlisted=True)
            
            # Create CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="applications_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            
            # Write header
            writer.writerow([
                'Application ID', 'Applicant Name', 'Email', 'Phone', 'Job Title',
                'Company', 'Status', 'Match Score', 'Rating', 'Applied Date',
                'Last Activity', 'Shortlisted'
            ])
            
            # Write data
            for app in queryset:
                writer.writerow([
                    str(app.id),
                    app.applicant.personal_profile.full_name if hasattr(app.applicant, 'personal_profile') else '',
                    app.applicant.email,
                    app.applicant.personal_profile.phone if hasattr(app.applicant, 'personal_profile') else '',
                    app.job.title,
                    app.job.company.company_name,
                    app.get_status_display(),
                    app.match_score or '',
                    app.rating or '',
                    app.applied_at.strftime('%Y-%m-%d'),
                    app.last_activity_at.strftime('%Y-%m-%d %H:%M'),
                    'Yes' if app.is_shortlisted else 'No'
                ])
            
            logger.info(f"Applications exported by user {request.user.id}")
            return response
            
        except Exception as e:
            logger.error(f"Error exporting applications: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred while exporting applications.")
            return redirect('applications:manage')


# ===========================
# Shared Views
# ===========================

class ApplicationStatsView(LoginRequiredMixin, View):
    """View for application statistics."""

    def get(self, request, *args, **kwargs):
        """Display application statistics."""
        if request.user.account_type == 'personal':
            # Personal user stats
            applications = Application.objects.filter(
                applicant=request.user
            ).select_related('job')
            
            stats = {
                'total_applications': applications.count(),
                'active_applications': applications.filter(status__in=[
                    ApplicationStatus.PENDING,
                    ApplicationStatus.SCREENING,
                    ApplicationStatus.INTERVIEW,
                    ApplicationStatus.OFFER
                ]).count(),
                'pending': applications.filter(status=ApplicationStatus.PENDING).count(),
                'screening': applications.filter(status=ApplicationStatus.SCREENING).count(),
                'interview': applications.filter(status=ApplicationStatus.INTERVIEW).count(),
                'offer': applications.filter(status=ApplicationStatus.OFFER).count(),
                'hired': applications.filter(status=ApplicationStatus.HIRED).count(),
                'rejected': applications.filter(status=ApplicationStatus.REJECTED).count(),
                'withdrawn': applications.filter(status=ApplicationStatus.WITHDRAWN).count(),
                'average_match_score': applications.exclude(match_score__isnull=True).aggregate(
                    avg_score=Avg('match_score')
                )['avg_score'] or 0,
            }
            
            template = 'applications/personal_stats.html'
            
        elif request.user.account_type == 'company':
            # Company user stats - ✅ FIXED query
            applications = Application.objects.filter(
                job__company__user=request.user
            ).select_related('job', 'applicant')
            
            stats = {
                'total_applications': applications.count(),
                'active_applications': applications.filter(status__in=[
                    ApplicationStatus.PENDING,
                    ApplicationStatus.SCREENING,
                    ApplicationStatus.INTERVIEW,
                    ApplicationStatus.OFFER
                ]).count(),
                'pending': applications.filter(status=ApplicationStatus.PENDING).count(),
                'screening': applications.filter(status=ApplicationStatus.SCREENING).count(),
                'interview': applications.filter(status=ApplicationStatus.INTERVIEW).count(),
                'offer': applications.filter(status=ApplicationStatus.OFFER).count(),
                'hired': applications.filter(status=ApplicationStatus.HIRED).count(),
                'rejected': applications.filter(status=ApplicationStatus.REJECTED).count(),
                'withdrawn': applications.filter(status=ApplicationStatus.WITHDRAWN).count(),
                'average_match_score': applications.exclude(match_score__isnull=True).aggregate(
                    avg_score=Avg('match_score')
                )['avg_score'] or 0,
                'high_priority': applications.filter(
                    Q(match_score__gte=80) | Q(is_shortlisted=True)
                ).count(),
                'shortlisted': applications.filter(is_shortlisted=True).count(),
            }
            
            template = 'applications/company_stats.html'
        else:
            return HttpResponseForbidden("Invalid account type")
        
        return render(request, template, {'stats': stats})


class CompanyPipelineDataView(LoginRequiredMixin, View):
    """AJAX endpoint exposing company pipeline metrics."""

    def get(self, request, *args, **kwargs):
        if request.user.account_type != 'company':
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        queryset = Application.objects.filter(job__company=request.user.company_profile)
        pipeline = build_pipeline_data(queryset)
        return JsonResponse({'success': True, 'pipeline': pipeline})


# ===========================
# AJAX Views
# ===========================

class ApplicationStatusUpdateView(LoginRequiredMixin, View):
    """AJAX view for updating application status."""

    @transaction.atomic  # ✅ Add transaction handling
    def post(self, request, *args, **kwargs):
        """Handle AJAX status update."""
        try:
            pk = kwargs.get('pk')
            application = get_object_or_404(
                Application.objects.select_related('job', 'job__company'),
                pk=pk,
                job__company__user=request.user
            )
            
            new_status = request.POST.get('status')
            
            application.update_status(new_status, request.user)
            
            logger.info(f"Application {application.id} status updated to {new_status} via AJAX")
            
            pipeline_queryset = Application.objects.filter(
                job=application.job,
                job__company__user=request.user
            )
            pipeline_data = build_pipeline_data(pipeline_queryset)

            return JsonResponse({
                'success': True,
                'message': 'Status updated successfully',
                'new_status': application.status,
                'status_display': application.get_status_display(),
                'pipeline': pipeline_data
            })
        except Exception as e:
            logger.error(f"Error in AJAX status update: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)


class ApplicationShortlistToggleView(LoginRequiredMixin, View):
    """AJAX view for toggling shortlist status."""

    def post(self, request, *args, **kwargs):
        """Handle AJAX shortlist toggle."""
        try:
            pk = kwargs.get('pk')
            application = get_object_or_404(
                Application,
                pk=pk,
                job__company__user=request.user
            )
            
            application.toggle_shortlist()
            
            logger.info(f"Application {application.id} shortlist toggled to {application.is_shortlisted}")
            
            return JsonResponse({
                'success': True,
                'is_shortlisted': application.is_shortlisted
            })
        except Exception as e:
            logger.error(f"Error in AJAX shortlist toggle: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)


class ApplicationNoteCreateAJAXView(LoginRequiredMixin, View):
    """AJAX view for creating notes."""

    @transaction.atomic  # ✅ Add transaction handling
    def post(self, request, *args, **kwargs):
        """Handle AJAX note creation."""
        try:
            pk = kwargs.get('pk')
            application = get_object_or_404(
                Application,
                pk=pk,
                job__company__user=request.user
            )
            
            note_text = request.POST.get('note')
            is_important = request.POST.get('is_important', 'false').lower() == 'true'
            
            if not note_text:
                return JsonResponse({
                    'success': False,
                    'message': 'Note text is required'
                }, status=400)
            
            note = ApplicationNote.objects.create(
                application=application,
                author=request.user,
                note=note_text,
                is_important=is_important
            )
            
            logger.info(f"Note created for application {application.id} via AJAX")
            
            return JsonResponse({
                'success': True,
                'note': {
                    'id': str(note.id),
                    'text': note.note,
                    'author': note.author.personal_profile.full_name if hasattr(note.author, 'personal_profile') else note.author.email,
                    'created_at': note.created_at.isoformat(),
                    'is_important': note.is_important
                }
            })
        except Exception as e:
            logger.error(f"Error in AJAX note creation: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)


# ===========================
# Resume Access Views for Applications
# ===========================

@method_decorator(company_account_required, name='dispatch')
class ApplicationResumeDownloadView(BaseResumeDownloadView):
    """View for companies to download applicant resumes."""

    def get_queryset(self):
        """Override to allow access to resumes of applicants for company's jobs."""
        return Resume.objects.filter(
            applications__job__company__user=self.request.user
        ).distinct()

    def get_object(self, queryset=None):
        """Override to use uuid field for lookup."""
        if queryset is None:
            queryset = self.get_queryset()
        
        # Use uuid field for lookup instead of pk
        uuid = self.kwargs.get('pk')
        return get_object_or_404(queryset, uuid=uuid)


@method_decorator(company_account_required, name='dispatch')
class ApplicationResumePreviewView(BaseResumePreviewView):
    """View for companies to preview applicant resumes."""

    def get_queryset(self):
        """Override to allow access to resumes of applicants for company's jobs."""
        return Resume.objects.filter(
            applications__job__company__user=self.request.user
        ).distinct()

    def get_object(self, queryset=None):
        """Override to use uuid field for lookup."""
        if queryset is None:
            queryset = self.get_queryset()
        
        # Use uuid field for lookup instead of pk
        uuid = self.kwargs.get('pk')
        return get_object_or_404(queryset, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        back_url = self.request.GET.get('next')
        if back_url:
            context['back_url'] = back_url
        return context
