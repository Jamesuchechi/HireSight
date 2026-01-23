import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.applications.models import Application


class InterviewQuerySet(models.QuerySet):
    """Reusable queryset with interview-specific filters."""

    def upcoming(self):
        """Get all upcoming interviews."""
        return self.filter(
            scheduled_date__gte=timezone.now(),
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED]
        )

    def past(self):
        """Get all past interviews."""
        return self.filter(
            scheduled_date__lt=timezone.now()
        ).exclude(status=Interview.InterviewStatus.CANCELLED)

    def for_company(self, company_user):
        """Return interviews belonging to the given company user."""
        return self.filter(application__job__company__user=company_user)

    def for_candidate(self, candidate_user):
        """Return interviews belonging to the given candidate user."""
        return self.filter(application__applicant=candidate_user)

    def needing_24h_reminder(self):
        """Get interviews that need a 24-hour reminder."""
        window_start = timezone.now() + timedelta(hours=24) - timedelta(minutes=15)
        window_end = timezone.now() + timedelta(hours=24) + timedelta(minutes=15)
        return self.filter(
            scheduled_date__range=(window_start, window_end),
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED],
            reminder_24h_sent=False
        )

    def needing_1h_reminder(self):
        """Get interviews that need a 1-hour reminder."""
        window_start = timezone.now() + timedelta(hours=1) - timedelta(minutes=15)
        window_end = timezone.now() + timedelta(hours=1) + timedelta(minutes=15)
        return self.filter(
            scheduled_date__range=(window_start, window_end),
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED],
            reminder_1h_sent=False
        )


class InterviewManager(models.Manager.from_queryset(InterviewQuerySet)):
    """Manager that exposes the interview queryset helpers."""


class Interview(models.Model):
    """
    Interview scheduling and management model
    
    Handles all aspects of interview scheduling, rescheduling, cancellation,
    and tracking between companies and candidates.
    """
    
    class InterviewStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        RESCHEDULED = 'RESCHEDULED', 'Rescheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'
    
    class InterviewType(models.TextChoices):
        PHONE = 'PHONE', 'Phone Screen'
        VIDEO = 'VIDEO', 'Video Call'
        ONSITE = 'ONSITE', 'On-site'
        TECHNICAL = 'TECHNICAL', 'Technical Assessment'
        BEHAVIORAL = 'BEHAVIORAL', 'Behavioral Interview'
        PANEL = 'PANEL', 'Panel Interview'
        CULTURE_FIT = 'CULTURE_FIT', 'Culture Fit Interview'
        FINAL = 'FINAL', 'Final Interview'
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='interviews'
    )
    interview_type = models.CharField(
        max_length=20, 
        choices=InterviewType.choices,
        help_text='Type of interview being conducted'
    )
    status = models.CharField(
        max_length=20, 
        choices=InterviewStatus.choices, 
        default=InterviewStatus.SCHEDULED
    )
    
    # Scheduling details
    scheduled_date = models.DateTimeField(
        help_text='Date and time of the interview'
    )
    duration_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(480)],
        help_text='Interview duration in minutes (15-480)'
    )
    timezone_name = models.CharField(
        max_length=50, 
        default='UTC',
        help_text='Timezone for the scheduled date (e.g., America/New_York)',
        db_column='timezone'
    )
    
    # Location details
    location = models.CharField(
        max_length=255, 
        blank=True,
        help_text='Physical location for on-site interviews'
    )
    video_link = models.URLField(
        blank=True, 
        validators=[URLValidator()],
        help_text='Video call link (Zoom, Google Meet, etc.)'
    )
    dial_in_number = models.CharField(
        max_length=50, 
        blank=True,
        help_text='Phone number for dial-in option'
    )
    
    # Interviewer details
    interviewer_name = models.CharField(
        max_length=255,
        help_text='Primary interviewer name'
    )
    interviewer_email = models.EmailField(
        help_text='Primary interviewer email'
    )
    additional_interviewers = models.JSONField(
        default=list, 
        blank=True,
        help_text='List of additional interviewers: [{"name": "...", "email": "..."}]'
    )
    
    # Notes and instructions
    company_notes = models.TextField(
        blank=True,
        help_text='Internal notes for the company (not visible to candidate)'
    )
    candidate_instructions = models.TextField(
        blank=True,
        help_text='Instructions sent to the candidate'
    )
    completion_notes = models.TextField(
        blank=True,
        help_text='Notes added after interview completion'
    )
    no_show_contacted_candidate = models.BooleanField(
        default=False,
        help_text='Whether the recruiter tried contacting the candidate before marking no-show'
    )
    
    # Rating and feedback (post-interview)
    interview_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Interview rating (1-5 stars)'
    )
    interviewer_feedback = models.TextField(
        blank=True,
        help_text='Detailed feedback from interviewer'
    )
    
    # Reminder tracking
    reminder_24h_sent = models.BooleanField(
        default=False,
        help_text='Whether 24-hour reminder has been sent'
    )
    reminder_1h_sent = models.BooleanField(
        default=False,
        help_text='Whether 1-hour reminder has been sent'
    )
    
    # Cancellation details
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cancelled_interviews'
    )
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Rescheduling tracking
    original_scheduled_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Original scheduled date before any rescheduling'
    )
    reschedule_count = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(5)],
        help_text='Number of times this interview has been rescheduled'
    )
    feedback_template = models.ForeignKey(
        'InterviewFeedbackTemplate',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='interviews'
    )
    candidate_response = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Response'),
            ('ACCEPTED', 'Accepted'),
            ('DECLINED', 'Declined'),
            ('PROPOSED_RESCHEDULE', 'Proposed Reschedule'),
        ],
        default='PENDING',
        help_text='Candidate response to interview invitation'
    )
    proposed_times = models.JSONField(
        default=list,
        blank=True,
        help_text='Candidate-proposed alternative times: [{"date": "...", "reason": "..."}]'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_interviews'
    )
    
    objects = InterviewManager()
    
    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
        ]
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'
    
    def __str__(self):
        return f"{self.get_interview_type_display()} - {self.application.applicant.email} - {self.scheduled_date}"
    
    def clean(self):
        """Validate the interview data"""
        super().clean()
        
        # Ensure scheduled date is in the future when creating
        if not self.pk and self.scheduled_date:
            if self.scheduled_date <= timezone.now():
                raise ValidationError({
                    'scheduled_date': 'Interview must be scheduled in the future'
                })
        
        # Validate video link for video interviews
        if self.interview_type == self.InterviewType.VIDEO and not self.video_link:
            raise ValidationError({
                'video_link': 'Video link is required for video interviews'
            })
        
        # Validate location for on-site interviews
        if self.interview_type == self.InterviewType.ONSITE and not self.location:
            raise ValidationError({
                'location': 'Location is required for on-site interviews'
            })
        
        # Validate reschedule count
        if self.reschedule_count > 5:
            raise ValidationError({
                'reschedule_count': 'Interview cannot be rescheduled more than 5 times'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_end_time(self):
        """Calculate and return the end time of the interview"""
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)
    
    def can_reschedule(self):
        """Check if interview can be rescheduled"""
        return (
            self.status in {self.InterviewStatus.SCHEDULED, self.InterviewStatus.RESCHEDULED}
            and self.reschedule_count < 5
            and self.scheduled_date > timezone.now()
        )
    
    def can_cancel(self):
        """Check if interview can be cancelled"""
        return (
            self.status not in {self.InterviewStatus.CANCELLED, self.InterviewStatus.COMPLETED}
            and self.scheduled_date > timezone.now()
        )
    
    def can_mark_completed(self):
        """Check if interview can be marked as completed"""
        return (
            self.status in {self.InterviewStatus.SCHEDULED, self.InterviewStatus.RESCHEDULED}
            and self.scheduled_date <= timezone.now()
        )
    
    def is_upcoming(self):
        """Check if interview is upcoming"""
        return (
            self.scheduled_date > timezone.now()
            and self.status in {self.InterviewStatus.SCHEDULED, self.InterviewStatus.RESCHEDULED}
        )
    
    def time_until_interview(self):
        """Get time remaining until interview"""
        if self.scheduled_date > timezone.now():
            return self.scheduled_date - timezone.now()
        return None
    
    def duration_display(self):
        """Human-readable duration"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours and minutes:
            return f"{hours}h {minutes}m"
        elif hours:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    def get_all_interviewers(self):
        """Get list of all interviewers (primary + additional)"""
        interviewers = [{
            'name': self.interviewer_name,
            'email': self.interviewer_email,
            'is_primary': True
        }]
        
        for interviewer in self.additional_interviewers:
            interviewers.append({
                'name': interviewer.get('name'),
                'email': interviewer.get('email'),
                'is_primary': False
            })
        
        return interviewers
    
    def get_calendar_event_url(self):
        """Generate Google Calendar event URL"""
        from urllib.parse import urlencode

        params = {
            'action': 'TEMPLATE',
            'text': f"Interview: {self.application.job.title}",
            'dates': f"{self.scheduled_date.strftime('%Y%m%dT%H%M%SZ')}/{self.get_end_time().strftime('%Y%m%dT%H%M%SZ')}",
            'details': self.candidate_instructions or f"Interview for {self.application.job.title}",
            'location': self.location or self.video_link or 'Online',
        }
        
        return f"https://calendar.google.com/calendar/render?{urlencode(params)}"

    def to_archive_payload(self):
        """Serialize the interview payload for long term archives"""
        return {
            'interview_type': self.interview_type,
            'status': self.status,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'duration_minutes': self.duration_minutes,
            'timezone_name': self.timezone_name,
            'location': self.location,
            'video_link': self.video_link,
            'dial_in_number': self.dial_in_number,
            'interviewer_name': self.interviewer_name,
            'interviewer_email': self.interviewer_email,
            'additional_interviewers': self.additional_interviewers,
            'company_notes': self.company_notes,
            'candidate_instructions': self.candidate_instructions,
            'completion_notes': self.completion_notes,
            'interview_rating': self.interview_rating,
            'interviewer_feedback': self.interviewer_feedback,
            'reminder_24h_sent': self.reminder_24h_sent,
            'reminder_1h_sent': self.reminder_1h_sent,
            'cancellation_reason': self.cancellation_reason,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'original_scheduled_date': self.original_scheduled_date.isoformat() if self.original_scheduled_date else None,
            'reschedule_count': self.reschedule_count,
            'candidate_response': self.candidate_response,
            'proposed_times': self.proposed_times,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'no_show_contacted_candidate': self.no_show_contacted_candidate,
        }


class InterviewFeedbackTemplate(models.Model):
    """Reusable feedback templates for interviews."""

    company = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_feedback_templates'
    )
    name = models.CharField(max_length=200)
    interview_type = models.CharField(
        max_length=20,
        choices=Interview.InterviewType.choices
    )
    questions = models.JSONField(
        help_text='List of questions: [{"question": "...", "type": "text|rating|boolean"}]'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.company} / {self.name}"


class InterviewActivityLog(models.Model):
    """Audit log of interview-level actions that need historical tracking."""

    class ActionChoices(models.TextChoices):
        RESCHEDULED = 'RESCHEDULED', 'Rescheduled'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'
        COMPLETED = 'COMPLETED', 'Completed'

    interview = models.ForeignKey(
        Interview,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activity_logs'
    )
    action = models.CharField(
        max_length=20,
        choices=ActionChoices.choices,
        help_text='Type of interview action'
    )
    notes = models.TextField(
        blank=True,
        help_text='Optional notes describing the event'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Structured metadata for the logged event'
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='interview_activity_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ArchivedInterview(models.Model):
    """Lightweight archive record for interviews older than a retention window."""

    interview_id = models.UUIDField(primary_key=True, editable=False)
    application = models.ForeignKey(
        Application,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='archived_interviews'
    )
    company = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='archived_interviews'
    )
    job_title = models.CharField(max_length=255)
    applicant_email = models.EmailField()
    status = models.CharField(max_length=20, choices=Interview.InterviewStatus.choices)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField()

    class Meta:
        ordering = ['-archived_at']
