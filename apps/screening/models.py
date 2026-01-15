"""
Models for screening system - FIXED VERSION with proper imports.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
from django.db.models import Q, JSONField, Avg  
from django.urls import reverse


class ScreeningStatus(models.TextChoices):
    """Screening session status choices."""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class ScreeningSessionManager(models.Manager):
    """Custom manager for ScreeningSession model."""

    def for_company(self, company):
        """Get screening sessions for a specific company."""
        return self.filter(company=company)

    def recent(self, days=30):
        """Get recent screening sessions."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)

    def completed(self):
        """Get completed screening sessions."""
        return self.filter(status=ScreeningStatus.COMPLETED)

    def in_progress(self):
        """Get screening sessions currently in progress."""
        return self.filter(status__in=[ScreeningStatus.PENDING, ScreeningStatus.PROCESSING])


class ScreeningSession(models.Model):
    """AI screening session model."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Company
    company = models.ForeignKey(
        'accounts.CompanyProfile',
        on_delete=models.CASCADE,
        related_name='screening_sessions'
    )

    # Job (optional - can be general screening or for specific job)
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='screening_sessions',
        help_text="Specific job being screened for (optional)"
    )

    # Session Information
    title = models.CharField(
        max_length=200,
        help_text="Session name/description"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_screening_sessions',
        help_text="Who initiated the screening session"
    )

    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=ScreeningStatus.choices,
        default=ScreeningStatus.PENDING,
        db_index=True,
        help_text="Current screening status"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When screening session was created"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When screening session was completed"
    )

    # Statistics
    total_resumes = models.PositiveIntegerField(
        default=0,
        help_text="Total number of resumes in session"
    )
    processed_resumes = models.PositiveIntegerField(
        default=0,
        help_text="Number of resumes processed successfully"
    )
    failed_resumes = models.PositiveIntegerField(
        default=0,
        help_text="Number of resumes that failed processing"
    )
    average_match_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Average match score across all resumes"
    )

    # Settings
    settings = JSONField(
        default=dict,
        blank=True,
        help_text="Screening parameters and settings"
    )

    # Custom manager
    objects = ScreeningSessionManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['job', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        """Get screening session detail URL."""
        return reverse('screening:session_detail', kwargs={'pk': self.pk})

    @property
    def progress_percentage(self):
        """Calculate progress percentage."""
        if self.total_resumes == 0:
            return 0
        return (self.processed_resumes / self.total_resumes) * 100

    @property
    def success_rate(self):
        """Calculate success rate."""
        if self.total_resumes == 0:
            return 0
        return (self.processed_resumes / self.total_resumes) * 100

    @property
    def failure_rate(self):
        """Calculate failure rate."""
        if self.total_resumes == 0:
            return 0
        return (self.failed_resumes / self.total_resumes) * 100

    def start_processing(self):
        """Mark session as processing."""
        self.status = ScreeningStatus.PROCESSING
        self.save(update_fields=['status'])

    def mark_completed(self):
        """Mark session as completed."""
        self.status = ScreeningStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def mark_failed(self):
        """Mark session as failed."""
        self.status = ScreeningStatus.FAILED
        self.save(update_fields=['status'])

    def update_statistics(self):
        """Update session statistics based on results."""
        results = self.results.filter(status=ScreeningResultStatus.COMPLETED)
        
        self.total_resumes = self.results.count()
        self.processed_resumes = results.count()
        self.failed_resumes = self.results.filter(status=ScreeningResultStatus.FAILED).count()
        
        # Calculate average match score
        avg_score = results.aggregate(avg_score=Avg('match_score'))['avg_score']
        
        self.average_match_score = avg_score
        self.save()


class ScreeningResultStatus(models.TextChoices):
    """Screening result status choices."""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class ScreeningResultManager(models.Manager):
    """Custom manager for ScreeningResult model."""

    def for_session(self, session):
        """Get results for a specific screening session."""
        return self.filter(session=session)

    def completed(self):
        """Get completed screening results."""
        return self.filter(status=ScreeningResultStatus.COMPLETED)

    def high_matches(self, threshold=80):
        """Get high match score results."""
        return self.filter(match_score__gte=threshold)

    def by_resume(self, resume):
        """Get screening results for a specific resume."""
        return self.filter(resume=resume)


class ScreeningResult(models.Model):
    """AI screening result for a single resume."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    session = models.ForeignKey(
        ScreeningSession,
        on_delete=models.CASCADE,
        related_name='results'
    )
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.CASCADE,
        null=True,  # Allow null initially
        related_name='screening_results'
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='screening_results',
        help_text="Job being matched against (if applicable)"
    )

    # Match Score
    match_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI-generated match score (0-100)"
    )

    # Detailed Match Analysis
    match_details = JSONField(
        default=dict,
        blank=True,
        help_text="Detailed match analysis"
    )

    # File Path
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to uploaded resume file"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ScreeningResultStatus.choices,
        default=ScreeningResultStatus.PENDING,
        db_index=True,
        help_text="Processing status"
    )

    # Timestamps
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When screening was completed"
    )

    # Error Information
    error_message = models.TextField(
        blank=True,
        help_text="Error message if processing failed"
    )

    # Recruiter Actions
    is_shortlisted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Has this candidate been shortlisted?"
    )
    notes = models.TextField(
        blank=True,
        help_text="Recruiter notes about this screening result"
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Manual rating (1-5)"
    )

    # Custom manager
    objects = ScreeningResultManager()

    class Meta:
        ordering = ['-match_score', '-processed_at']
        indexes = [
            models.Index(fields=['session', '-match_score']),
            models.Index(fields=['resume', '-match_score']),
            models.Index(fields=['status', '-processed_at']),
            models.Index(fields=['is_shortlisted', '-match_score']),
        ]
        constraints = [
            models.CheckConstraint(
                name='screening_match_score_range',
                condition=Q(match_score__gte=0) & Q(match_score__lte=100)
            ),
            models.CheckConstraint(
                name='screening_rating_range',
                condition=Q(rating__isnull=True) | (Q(rating__gte=1) & Q(rating__lte=5))
            ),
        ]

    def __str__(self):
        if self.resume:
            return f"{self.resume.user.email} - {self.match_score}% match"
        return f"Result {str(self.id)[:8]} - {self.match_score}% match"

    def mark_as_processing(self):
        """Mark result as processing."""
        self.status = ScreeningResultStatus.PROCESSING
        self.save(update_fields=['status'])

    def mark_as_completed(self):
        """Mark result as completed."""
        self.status = ScreeningResultStatus.COMPLETED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])

    def mark_as_failed(self, error_message):
        """Mark result as failed."""
        self.status = ScreeningResultStatus.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def toggle_shortlist(self):
        """Toggle shortlist status."""
        self.is_shortlisted = not self.is_shortlisted
        self.save(update_fields=['is_shortlisted'])

    @property
    def skills_match(self):
        """Get skills match details."""
        return self.match_details.get('skills_match', {})

    @property
    def skills_gaps(self):
        """Get skills gaps."""
        skills_match = self.match_details.get('skills_match', {})
        return skills_match.get('missing', [])

    @property
    def experience_match(self):
        """Get experience match score."""
        return self.match_details.get('experience_match', 0)

    @property
    def education_match(self):
        """Get education match score."""
        return self.match_details.get('education_match', 0)

    @property
    def semantic_similarity(self):
        """Get semantic similarity score."""
        return self.match_details.get('semantic_similarity', 0)


class ScreeningCriteria(models.Model):
    """Customizable screening criteria for a session."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship
    session = models.OneToOneField(
        ScreeningSession,
        on_delete=models.CASCADE,
        related_name='criteria'
    )

    # Skills Requirements
    required_skills = JSONField(
        default=list,
        blank=True,
        help_text="List of required skills"
    )
    nice_to_have_skills = JSONField(
        default=list,
        blank=True,
        help_text="List of nice-to-have skills"
    )

    # Experience Requirements
    min_experience_years = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum years of experience required"
    )
    max_experience_years = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum years of experience (optional)"
    )

    # Education Requirements
    required_education = JSONField(
        default=list,
        blank=True,
        help_text="Required education levels"
    )

    # Location Preferences
    location_preference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Preferred location (optional)"
    )

    # Custom Keywords
    custom_keywords = JSONField(
        default=list,
        blank=True,
        help_text="Custom keywords to match"
    )

    # Scoring Weights
    weight_skills = models.FloatField(
        default=0.4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for skills in scoring (0-1)"
    )
    weight_experience = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for experience in scoring (0-1)"
    )
    weight_education = models.FloatField(
        default=0.2,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for education in scoring (0-1)"
    )
    weight_keywords = models.FloatField(
        default=0.1,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for keywords in scoring (0-1)"
    )

    class Meta:
        verbose_name_plural = 'Screening Criteria'

    def __str__(self):
        return f"Criteria for {self.session.title}"

    def validate_weights(self):
        """Validate that weights sum to 1."""
        total = (self.weight_skills + self.weight_experience + 
                self.weight_education + self.weight_keywords)
        
        if not (0.99 <= total <= 1.01):  # Allow small floating point rounding
            raise ValidationError("Weights must sum to 1.0")

    def save(self, *args, **kwargs):
        """Override save to validate weights."""
        self.validate_weights()
        super().save(*args, **kwargs)


class PipelineStatus(models.TextChoices):
    """Pipeline push status choices."""
    PENDING = 'pending', 'Pending'
    PUSHED = 'pushed', 'Pushed to Pipeline'
    REJECTED = 'rejected', 'Rejected from Pipeline'
    HIRED = 'hired', 'Hired'
    WITHDRAWN = 'withdrawn', 'Withdrawn'


class PipelineIntegration(models.Model):
    """Track candidate pushes to job pipeline."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    result = models.OneToOneField(
        ScreeningResult,
        on_delete=models.CASCADE,
        related_name='pipeline_integration'
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Job being applied for"
    )
    company = models.ForeignKey(
        'accounts.CompanyProfile',
        on_delete=models.CASCADE,
        related_name='pipeline_integrations'
    )

    # Pipeline Status
    status = models.CharField(
        max_length=20,
        choices=PipelineStatus.choices,
        default=PipelineStatus.PENDING,
        db_index=True,
        help_text="Current pipeline status"
    )

    # Timestamps
    pushed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When candidate was pushed to pipeline"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )

    # Pipeline Details
    pipeline_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External pipeline system ID (if applicable)"
    )
    pipeline_url = models.URLField(
        blank=True,
        help_text="Link to candidate in pipeline system"
    )

    # Stage Information
    pipeline_stage = models.CharField(
        max_length=100,
        blank=True,
        help_text="Current stage in hiring pipeline"
    )
    stage_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When stage was last updated"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Notes about pipeline integration"
    )

    # Sync Information
    last_synced = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time data was synced with pipeline"
    )
    sync_failed = models.BooleanField(
        default=False,
        help_text="Has sync with pipeline failed?"
    )
    sync_error = models.TextField(
        blank=True,
        help_text="Sync error details if failed"
    )

    class Meta:
        ordering = ['-pushed_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['company', '-pushed_at']),
            models.Index(fields=['status', '-pushed_at']),
        ]
        verbose_name_plural = 'Pipeline Integrations'

    def __str__(self):
        return f"{self.result} → {self.get_status_display()}"

    def mark_as_hired(self):
        """Mark candidate as hired."""
        self.status = PipelineStatus.HIRED
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_rejected(self):
        """Mark candidate as rejected."""
        self.status = PipelineStatus.REJECTED
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])

    def mark_sync_failed(self, error):
        """Mark sync as failed."""
        self.sync_failed = True
        self.sync_error = str(error)
        self.save(update_fields=['sync_failed', 'sync_error'])

    def mark_sync_success(self):
        """Mark sync as successful."""
        self.sync_failed = False
        self.sync_error = ''
        self.last_synced = timezone.now()
        self.save(update_fields=['sync_failed', 'sync_error', 'last_synced'])


class ProgressUpdateType(models.TextChoices):
    """Types of progress updates."""
    UPLOAD_STARTED = 'upload_started', 'Upload Started'
    UPLOAD_PROGRESS = 'upload_progress', 'Upload Progress'
    UPLOAD_COMPLETED = 'upload_completed', 'Upload Completed'
    SCREENING_STARTED = 'screening_started', 'Screening Started'
    SCREENING_PROGRESS = 'screening_progress', 'Screening Progress'
    SCREENING_COMPLETED = 'screening_completed', 'Screening Completed'
    RESULT_ANALYZED = 'result_analyzed', 'Result Analyzed'
    PIPELINE_PUSHED = 'pipeline_pushed', 'Pushed to Pipeline'
    STATUS_CHANGED = 'status_changed', 'Status Changed'
    ERROR_OCCURRED = 'error_occurred', 'Error Occurred'


class ProgressUpdate(models.Model):
    """Real-time progress updates for screening sessions."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    session = models.ForeignKey(
        ScreeningSession,
        on_delete=models.CASCADE,
        related_name='progress_updates'
    )
    result = models.ForeignKey(
        ScreeningResult,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='progress_updates',
        help_text="Specific result (if applicable)"
    )

    # Update Information
    update_type = models.CharField(
        max_length=50,
        choices=ProgressUpdateType.choices,
        db_index=True,
        help_text="Type of progress update"
    )

    # Progress Details
    title = models.CharField(
        max_length=200,
        help_text="Human-readable update title"
    )
    message = models.TextField(
        blank=True,
        help_text="Detailed message about progress"
    )

    # Progress Metrics
    progress_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress percentage (0-100)"
    )
    current_item = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Current item being processed"
    )
    total_items = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total items to process"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('paused', 'Paused'),
        ],
        default='running',
        db_index=True,
        help_text="Update status"
    )

    # Error Information
    error_message = models.TextField(
        blank=True,
        help_text="Error message if applicable"
    )

    # Metadata
    metadata = JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata as JSON"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When update was created"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['update_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
        verbose_name_plural = 'Progress Updates'

    def __str__(self):
        return f"{self.session.title} - {self.get_update_type_display()}"

    @classmethod
    def create_update(cls, session, update_type, title, message='', **kwargs):
        """Create a progress update."""
        return cls.objects.create(
            session=session,
            update_type=update_type,
            title=title,
            message=message,
            **kwargs
        )

    def mark_completed(self):
        """Mark update as completed."""
        self.status = 'completed'
        self.progress_percent = 100
        self.save(update_fields=['status', 'progress_percent'])

    def mark_failed(self, error_message):
        """Mark update as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])


# ===========================
# AI Insight Models
# ===========================

class InsightType(models.TextChoices):
    """Types of AI insights available."""
    INTERVIEW_QUESTIONS = 'interview_questions', 'Interview Questions'
    NOTES = 'ai_notes', 'AI Notes'
    REJECTION_REASONS = 'rejection_reasons', 'Rejection Reasons'
    RESUME_PARSING = 'resume_parsing', 'Resume Parsing'


class AIInsight(models.Model):
    """Stores AI-generated insights for screening results."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    result = models.OneToOneField(
        ScreeningResult,
        on_delete=models.CASCADE,
        related_name='ai_insight',
        help_text='The screening result this insight is for'
    )

    # Insight Type
    insight_type = models.CharField(
        max_length=50,
        choices=InsightType.choices,
        help_text='Type of AI insight'
    )

    # Content
    title = models.CharField(
        max_length=255,
        help_text='Title of the insight'
    )

    content = models.JSONField(
        default=dict,
        help_text='Structured insight content (varies by type)'
    )

    summary = models.TextField(
        blank=True,
        default='',
        help_text='Plain text summary of the insight'
    )

    # Metadata
    model_used = models.CharField(
        max_length=50,
        default='mistral-7b',
        help_text='Mistral model version used'
    )

    tokens_used = models.IntegerField(
        default=0,
        help_text='Number of tokens used for generation'
    )

    generation_time = models.FloatField(
        default=0.0,
        help_text='Time in seconds to generate insight'
    )

    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text='Confidence score (0-1) of the AI insight'
    )

    # Status
    is_approved = models.BooleanField(
        default=False,
        help_text='Whether recruiter has approved this insight'
    )

    is_used = models.BooleanField(
        default=False,
        help_text='Whether this insight was actually used'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Insight'
        verbose_name_plural = 'AI Insights'
        indexes = [
            models.Index(fields=['result', 'insight_type'], name='ai_insight_result_type_idx'),
            models.Index(fields=['insight_type', '-created_at'], name='ai_insight_type_date_idx'),
            models.Index(fields=['is_approved', '-created_at'], name='ai_insight_approved_idx'),
        ]

    def __str__(self):
        return f"{self.get_insight_type_display()} - {self.title}"

    def get_content_by_type(self):
        """Get content formatted by type."""
        if self.insight_type == InsightType.INTERVIEW_QUESTIONS:
            return self.content.get('questions', [])
        elif self.insight_type == InsightType.NOTES:
            return self.content.get('notes', [])
        elif self.insight_type == InsightType.REJECTION_REASONS:
            return self.content.get('reasons', [])
        elif self.insight_type == InsightType.RESUME_PARSING:
            return self.content.get('parsed_data', {})
        return self.content

    def mark_approved(self):
        """Mark insight as approved by recruiter."""
        self.is_approved = True
        self.save(update_fields=['is_approved', 'updated_at'])

    def mark_used(self):
        """Mark insight as used in decision-making."""
        self.is_used = True
        self.save(update_fields=['is_used', 'updated_at'])


class InsightFeedback(models.Model):
    """Track feedback on AI insights for model improvement."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    insight = models.ForeignKey(
        AIInsight,
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text='The insight this feedback is for'
    )

    # Feedback
    FEEDBACK_CHOICES = [
        ('helpful', 'Helpful'),
        ('partially_helpful', 'Partially Helpful'),
        ('not_helpful', 'Not Helpful'),
        ('incorrect', 'Incorrect'),
    ]

    rating = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES,
        help_text='Rating of the insight'
    )

    comment = models.TextField(
        blank=True,
        default='',
        help_text='Optional detailed feedback'
    )

    # User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ai_insight_feedback',
        help_text='User who provided feedback'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Insight Feedback'
        verbose_name_plural = 'Insight Feedback'
        indexes = [
            models.Index(fields=['insight', '-created_at'], name='insight_feedback_idx'),
            models.Index(fields=['rating', '-created_at'], name='insight_rating_idx'),
        ]

    def __str__(self):
        return f"Feedback ({self.rating}) on {self.insight}"
