import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.applications.models import Application
class VideoMetrics(models.Model):
    """Persisted video analysis metrics for practice responses.

    Stores raw metrics JSON as received from client analyzers and provides
    convenience accessors for derived metrics used by scoring logic.
    """

    id = models.BigAutoField(primary_key=True)
    raw = models.JSONField(default=dict)
    eye_contact_percentage = models.FloatField(null=True, blank=True)
    head_stability_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"VideoMetrics {self.id}"

    def compute_derived(self):
        """Fill derived fields from raw JSON if available."""
        ec = self.raw.get('eye_contact', {}) or {}
        fw = ec.get('frames_with_contact')
        tf = ec.get('total_frames')
        try:
            if fw is not None and tf:
                self.eye_contact_percentage = round((float(fw) / float(tf)) * 100, 1)
            else:
                self.eye_contact_percentage = ec.get('percentage') or 0.0
        except Exception:
            self.eye_contact_percentage = 0.0

        hs = self.raw.get('head_stability', {}) or {}
        movement = hs.get('movement_pixels', hs.get('movement', 0)) or 0
        max_m = hs.get('max_movement_pixels', hs.get('max_movement', 100)) or 100
        try:
            ratio = float(movement) / float(max_m) if float(max_m) else 1.0
            score = 1.0 - ratio
            self.head_stability_score = max(0.0, min(1.0, round(score, 3)))
        except Exception:
            self.head_stability_score = 0.0

        return self


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


class InterviewPracticeSessionManager(models.Manager):
    def for_candidate(self, user):
        return self.filter(candidate=user)


class InterviewPracticeSession(models.Model):
    """Candidate-facing practice session backed by AI questions."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CREATED = 'CREATED', 'Created'
        IN_PROGRESS = 'IN_PROGRESS', 'In progress'
        REVIEW_PENDING = 'REVIEW_PENDING', 'Review pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class GenerationState(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In progress'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_practice_sessions',
        limit_choices_to={'account_type': 'personal'}
    )
    application = models.ForeignKey(
        Application,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='practice_sessions'
    )
    interview_type = models.CharField(
        max_length=20,
        choices=Interview.InterviewType.choices,
        default=Interview.InterviewType.PHONE
    )
    difficulty = models.CharField(
        max_length=50,
        default='Intermediate',
        help_text='AI difficulty tier (Beginner, Intermediate, Advanced)'
    )
    enable_video = models.BooleanField(
        default=True,
        help_text='Whether video analysis is part of this session'
    )
    focus_area = models.CharField(
        max_length=100,
        blank=True,
        help_text='Optional focus area (technical, behavioral, culture)'
    )
    focus_areas = models.JSONField(
        default=list,
        blank=True,
        help_text='Multi-select focus areas: leadership, technical, communication, etc.'
    )
    time_limit_per_question = models.PositiveIntegerField(
        default=2,
        choices=[(1, '1 minute'), (2, '2 minutes'), (3, '3 minutes')],
        help_text='Time limit per question in minutes'
    )
    video_analysis_enabled = models.BooleanField(
        default=True,
        help_text='Whether video analysis is enabled for this session'
    )
    warmup_completed = models.BooleanField(
        default=False,
        help_text='Whether the warmup flow has been completed'
    )
    camera_test_passed = models.BooleanField(
        default=False,
        help_text='Whether camera test was passed'
    )
    microphone_test_passed = models.BooleanField(
        default=False,
        help_text='Whether microphone test was passed'
    )
    test_question_completed = models.BooleanField(
        default=False,
        help_text='Whether test question was completed'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Percent complete'
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text='Serialized settings for this practice run'
    )

    warmup_question_prompt = models.TextField(
        blank=True, null=True, help_text="AI-generated warmup question."
    )
    warmup_question_state = models.CharField(
        max_length=20,
        choices=GenerationState.choices,
        default=GenerationState.PENDING,
        help_text="The generation state of the warmup question."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    question_generation_state = models.CharField(
        max_length=20,
        choices=GenerationState.choices,
        default=GenerationState.PENDING
    )
    report_generation_state = models.CharField(
        max_length=20,
        choices=GenerationState.choices,
        default=GenerationState.PENDING
    )

    @property
    def number_of_questions(self):
        return int(self.settings.get('number_of_questions', 5))

    @number_of_questions.setter
    def number_of_questions(self, value):
        settings_copy = dict(self.settings or {})
        settings_copy['number_of_questions'] = int(value)
        self.settings = settings_copy

    objects = InterviewPracticeSessionManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Practice session for {self.candidate.email} ({self.interview_type})"


class PracticeQuestion(models.Model):
    """AI-generated practice question for a candidate session."""

    session = models.ForeignKey(
        InterviewPracticeSession,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    prompt = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    difficulty = models.CharField(max_length=50, blank=True)
    evaluation_criteria = models.JSONField(
        default=list,
        blank=True,
        help_text='Guidance for scoring (clarity, structure, tone, etc.)'
    )
    order = models.PositiveIntegerField(default=1)
    ai_generated_at = models.DateTimeField(auto_now_add=True)
    ai_request_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Question #{self.order} ({self.category or 'General'})"


class PracticeResponse(models.Model):
    """Candidate response (text/video) to a practice question."""

    question = models.ForeignKey(
        PracticeQuestion,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    session = models.ForeignKey(
        InterviewPracticeSession,
        on_delete=models.CASCADE,
        related_name='session_responses',
        null=True,
        blank=True
    )
    text_response = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    video_metrics = models.JSONField(
        default=None,
        null=True,
        blank=True,
        help_text='Client-side video metrics JSON'
    )
    video_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Duration of the uploaded video in seconds'
    )
    ai_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    ai_feedback = models.TextField(blank=True)
    analysis = models.JSONField(
        default=dict,
        blank=True,
        help_text='Video analysis, focus/confidence metrics'
    )
    analysis_status = models.CharField(
        max_length=20,
        choices=InterviewPracticeSession.GenerationState.choices,
        default=InterviewPracticeSession.GenerationState.PENDING
    )
    analysis_request_id = models.CharField(max_length=255, blank=True)
    gaze_direction = models.CharField(
        max_length=50,
        blank=True,
        help_text='Detected gaze direction (aligned/away/offscreen)'
    )
    head_tilt = models.CharField(
        max_length=50,
        blank=True,
        help_text='Detected head tilt (up/down/left/right)'
    )
    attention_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Attention/confidence score from video analysis (0-100)'
    )
    video_analysis_metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text='Detailed video analysis metrics from client-side MediaPipe detection'
    )
    content_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Content relevance and quality score (0-100)'
    )
    delivery_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Delivery and structure score (0-100)'
    )
    presence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Presence and engagement score (0-100)'
    )
    strengths = models.JSONField(
        default=list,
        blank=True,
        help_text='Top strengths identified in the response'
    )
    improvements = models.JSONField(
        default=list,
        blank=True,
        help_text='Top areas for improvement identified in the response'
    )
    ai_scoring_model = models.CharField(
        max_length=255,
        blank=True,
        help_text='Name of the AI model used for scoring'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    @property
    def overall_score(self):
        """Compatibility alias that exposes the AI-generated score."""
        return self.ai_score

    @overall_score.setter
    def overall_score(self, value):
        self.ai_score = value

    class Meta:
        indexes = [
            models.Index(fields=['session']),
        ]

    def __str__(self):
        return f"Response #{self.id} to {self.question}"


class PracticePerformanceReport(models.Model):
    """Comprehensive summarization of performance across a practice session."""

    session = models.OneToOneField(
        InterviewPracticeSession,
        on_delete=models.CASCADE,
        related_name='performance_report'
    )
    overall_score = models.DecimalField(max_digits=5, decimal_places=2)
    overall_rating = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Overall rating out of 100'
    )
    category_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text='Category scores: {behavioral: 85, technical: 70, situational: 78}'
    )
    strengths = models.JSONField(default=list, blank=True)
    top_strengths = models.JSONField(
        default=list,
        blank=True,
        help_text='Top 3-5 strengths identified across all responses'
    )
    weaknesses = models.JSONField(default=list, blank=True)
    improvement_areas = models.JSONField(
        default=list,
        blank=True,
        help_text='Top 3-5 areas for improvement'
    )
    recommendations = models.TextField(blank=True)
    action_items = models.JSONField(
        default=list,
        blank=True,
        help_text='Specific, actionable items for next practice session'
    )
    next_practice_suggestions = models.JSONField(
        default=list,
        blank=True,
        help_text='Suggested questions/scenarios to practice'
    )
    performance_trend = models.JSONField(
        default=dict,
        blank=True,
        help_text='Trend data showing improvement/decline'
    )
    ai_request_id = models.CharField(max_length=255, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.session}"


class PracticeMilestoneLog(models.Model):
    """Track practice session milestones that have already been celebrated."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_milestones'
    )
    milestone = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'milestone')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} milestone {self.milestone}"


class ConsentRecord(models.Model):
    """
    Records user consent for video recording and AI analysis in practice sessions.
    
    Tracks when users consent to video recording, data collection, and AI processing
    for audit and privacy compliance purposes.
    """
    
    class ConsentType(models.TextChoices):
        VIDEO_RECORDING = 'VIDEO_RECORDING', 'Video Recording'
        AI_ANALYSIS = 'AI_ANALYSIS', 'AI Analysis'
        DATA_STORAGE = 'DATA_STORAGE', 'Data Storage'
        PERFORMANCE_TRACKING = 'PERFORMANCE_TRACKING', 'Performance Tracking'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consent_records'
    )
    consent_type = models.CharField(
        max_length=50,
        choices=ConsentType.choices,
        help_text='Type of consent given'
    )
    granted = models.BooleanField(
        default=True,
        help_text='Whether consent was granted or declined'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        help_text='IP address of the user when consent was given'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='User agent string for device identification'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this consent expires (null = never)'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the consent'
    )
    
    class Meta:
        ordering = ['-granted_at']
        indexes = [
            models.Index(fields=['user', 'consent_type']),
            models.Index(fields=['granted_at']),
        ]
        unique_together = ('user', 'consent_type')
    
    def __str__(self):
        status = 'Granted' if self.granted else 'Declined'
        return f"{self.user.email} - {self.consent_type} ({status})"
    
    @property
    def is_active(self):
        """Check if consent is still active."""
        if not self.granted:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class AIUsageLog(models.Model):
    """
    Logs all AI API calls for monitoring, auditing, and cost tracking.
    
    Records information about each AI request including which model was used,
    tokens consumed, estimated costs, and associated user/session for billing
    and performance analysis.
    """
    
    class ModelType(models.TextChoices):
        GROQ = 'groq', 'Groq AI'
        MISTRAL = 'mistral', 'Mistral AI'
        OPENAI = 'openai', 'OpenAI GPT'
    
    class RequestType(models.TextChoices):
        QUESTION_GENERATION = 'question_gen', 'Question Generation'
        RESPONSE_SCORING = 'scoring', 'Response Scoring'
        REPORT_GENERATION = 'reporting', 'Report Generation'
        FEEDBACK = 'feedback', 'Feedback Generation'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_usage_logs'
    )
    session = models.ForeignKey(
        InterviewPracticeSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_usage_logs'
    )
    request_type = models.CharField(
        max_length=50,
        choices=RequestType.choices,
        help_text='Type of AI request'
    )
    model_used = models.CharField(
        max_length=50,
        choices=ModelType.choices,
        help_text='Which AI model was used'
    )
    input_tokens = models.PositiveIntegerField(
        default=0,
        help_text='Number of tokens in the request'
    )
    output_tokens = models.PositiveIntegerField(
        default=0,
        help_text='Number of tokens in the response'
    )
    total_tokens = models.PositiveIntegerField(
        default=0,
        help_text='Total tokens for this request'
    )
    estimated_cost_usd = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        default=0,
        help_text='Estimated cost in USD for this request'
    )
    response_time_ms = models.PositiveIntegerField(
        default=0,
        help_text='Response time in milliseconds'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('SUCCESS', 'Success'),
            ('PARTIAL', 'Partial Success'),
            ('FAILED', 'Failed'),
            ('FALLBACK', 'Fallback Used'),
        ],
        default='SUCCESS'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if request failed'
    )
    request_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Unique request ID from the API'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session']),
            models.Index(fields=['model_used']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_model_used_display()} - {self.get_request_type_display()} ({self.status})"
    
    @classmethod
    def log_request(cls, user, session, request_type, model_used, input_tokens=0, 
                   output_tokens=0, response_time_ms=0, status='SUCCESS', 
                   error_message='', request_id=''):
        """Create a log entry for an AI request."""
        total_tokens = input_tokens + output_tokens
        
        # Calculate estimated costs (these are example rates)
        cost_per_1k_tokens = {
            'groq': 0.0001,       # $0.0001 per 1k tokens (Groq is very cheap)
            'mistral': 0.0002,    # $0.0002 per 1k tokens
            'openai': 0.0015,     # $0.0015 per 1k tokens
        }
        
        rate = cost_per_1k_tokens.get(model_used, 0.001)
        estimated_cost = (total_tokens / 1000) * rate
        
        return cls.objects.create(
            user=user,
            session=session,
            request_type=request_type,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
            response_time_ms=response_time_ms,
            status=status,
            error_message=error_message,
            request_id=request_id
        )
