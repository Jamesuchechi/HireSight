import uuid
import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, JSONField
from django.urls import reverse

# Set up logging
logger = logging.getLogger(__name__)


class ApplicationStatus(models.TextChoices):
    """Application status choices."""
    PENDING = 'pending', 'Pending Review'
    SCREENING = 'screening', 'Under Screening'
    INTERVIEW = 'interview', 'Interview Scheduled'
    OFFER = 'offer', 'Offer Extended'
    HIRED = 'hired', 'Hired'
    REJECTED = 'rejected', 'Rejected'
    WITHDRAWN = 'withdrawn', 'Withdrawn'


class ApplicationManager(models.Manager):
    """Custom manager for Application model."""

    def for_job(self, job):
        """Get applications for a specific job."""
        return self.filter(job=job)

    def for_applicant(self, applicant):
        """Get applications by a specific applicant."""
        return self.filter(applicant=applicant)

    def active(self):
        """Get applications that are still active (not withdrawn/rejected/hired)."""
        return self.filter(
            status__in=[
                ApplicationStatus.PENDING,
                ApplicationStatus.SCREENING,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFER
            ]
        )

    def recent(self, days=30):
        """Get applications from the last N days."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(applied_at__gte=cutoff)

    def high_priority(self):
        """Get high-priority applications (high match score or shortlisted)."""
        return self.filter(
            Q(match_score__gte=80) | Q(is_shortlisted=True)
        )

    def search(self, query):
        """Search applications by applicant name, job title, or status."""
        return self.filter(
            Q(applicant__personal_profile__full_name__icontains=query) |
            Q(job__title__icontains=query) |
            Q(status__icontains=query)
        )


class Application(models.Model):
    """Job application model."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications',
        limit_choices_to={'account_type': 'personal'}
    )
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.SET_NULL,
        null=True,
        related_name='applications'
    )

    # Application Details
    cover_letter = models.TextField(
        blank=True,
        help_text="Optional cover letter"
    )
    portfolio_url = models.URLField(
        blank=True,
        help_text="Optional portfolio URL"
    )
    screening_answers = JSONField(
        default=dict,
        blank=True,
        help_text="Answers to screening questions"
    )
    additional_notes = models.TextField(
        blank=True,
        help_text="Applicant's additional notes"
    )

    # Status & Tracking
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        db_index=True,
        help_text="Current application status"
    )
    status_changed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When status was last changed"
    )
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes',
        help_text="Who changed the status"
    )

    # Match Score (from AI screening)
    match_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI-generated match score (0-100)"
    )
    match_details = JSONField(
        default=dict,
        blank=True,
        help_text="Detailed match analysis from AI"
    )
    screening_notes = models.TextField(
        blank=True,
        help_text="AI-generated screening notes"
    )

    # Company Internal
    recruiter_notes = models.TextField(
        blank=True,
        help_text="Private company notes about applicant"
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Recruiter rating (1-5)"
    )
    is_shortlisted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Is this applicant shortlisted?"
    )
    tags = JSONField(
        default=list,
        blank=True,
        help_text="Custom tags for organization"
    )

    # Rejection Feedback
    rejection_feedback = JSONField(
        null=True,
        blank=True,
        help_text="Feedback provided when rejecting the application"
    )

    # Timestamps
    applied_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When application was submitted"
    )
    viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When recruiter first viewed application"
    )
    last_activity_at = models.DateTimeField(
        auto_now=True,
        help_text="Last status change or note update"
    )
    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When application was withdrawn"
    )
    hired_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When applicant was hired"
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When application was rejected"
    )

    # Custom manager
    objects = ApplicationManager()

    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['job', '-applied_at']),
            models.Index(fields=['applicant', '-applied_at']),
            models.Index(fields=['status', '-applied_at']),
            models.Index(fields=['match_score', '-applied_at']),
            models.Index(fields=['is_shortlisted', '-applied_at']),
        ]
        constraints = [
            models.CheckConstraint(
                name='match_score_range',
                condition=Q(match_score__isnull=True) | (Q(match_score__gte=0) & Q(match_score__lte=100))
            ),
            models.CheckConstraint(
                name='rating_range',
                condition=Q(rating__isnull=True) | (Q(rating__gte=1) & Q(rating__lte=5))
            ),
            models.UniqueConstraint(
                fields=['job', 'applicant'],
                name='unique_application_per_job'
            ),
        ]

    def __str__(self):
        return f"{self.applicant.email} applied for {self.job.title}"

    def save(self, *args, **kwargs):
        """Override save to update timestamps and enforce business rules."""
        
        # Debug: Log the current state
        logger.debug(f"Saving application with pk={self.pk}, status={self.status}")
        
        # Update last_activity_at if status changed
        if self.pk:
            try:
                # Check if the application exists in the database
                if Application.objects.filter(pk=self.pk).exists():
                    original = Application.objects.get(pk=self.pk)
                    logger.debug(f"Found existing application: {original.status}")
                    if original.status != self.status:
                        self.last_activity_at = timezone.now()
                        
                        # Set specific timestamps based on status
                        if self.status == ApplicationStatus.WITHDRAWN:
                            self.withdrawn_at = timezone.now()
                        elif self.status == ApplicationStatus.HIRED:
                            self.hired_at = timezone.now()
                        elif self.status == ApplicationStatus.REJECTED:
                            self.rejected_at = timezone.now()
                else:
                    logger.debug(f"Application with pk={self.pk} does not exist in database yet")
            except Application.DoesNotExist:
                logger.debug(f"Application with pk={self.pk} does not exist - this is a new application")

        super().save(*args, **kwargs)
        
        # Debug: Log after save
        logger.debug(f"Application saved successfully with pk={self.pk}")

    def get_absolute_url(self):
        """Get application detail URL."""
        return reverse('applications:detail', kwargs={'pk': self.pk})

    @property
    def is_active(self):
        """Check if application is still active."""
        return self.status in [
            ApplicationStatus.PENDING,
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.OFFER
        ]

    @property
    def is_terminated(self):
        """Check if application has reached a terminal state."""
        return self.status in [
            ApplicationStatus.HIRED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN
        ]

    @property
    def can_withdraw(self):
        """Check if applicant can withdraw application."""
        return self.status in [
            ApplicationStatus.PENDING,
            ApplicationStatus.SCREENING
        ]

    @property
    def days_since_applied(self):
        """Get days since application was submitted."""
        delta = timezone.now() - self.applied_at
        return delta.days

    def update_status(self, new_status, changed_by=None):
        """Update application status with validation."""
        from .validators import validate_status_transition
        
        validate_status_transition(self.status, new_status)
        
        self.status = new_status
        self.status_changed_at = timezone.now()
        self.status_changed_by = changed_by
        self.save()

    def mark_as_viewed(self):
        """Mark application as viewed by recruiter."""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])

    def toggle_shortlist(self):
        """Toggle shortlist status."""
        self.is_shortlisted = not self.is_shortlisted
        self.save(update_fields=['is_shortlisted'])


class ApplicationStatusHistory(models.Model):
    """Audit trail for application status changes."""

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        null=True,
        blank=True,
        help_text="Previous status (NULL for initial status)"
    )
    new_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        help_text="New status"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='application_status_changes'
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for status change"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['application', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]

    def __str__(self):
        return f"{self.application} status changed from {self.old_status} to {self.new_status}"


class ApplicationNote(models.Model):
    """Internal communication and notes about applications."""

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='application_notes'
    )
    note = models.TextField(
        help_text="Note content"
    )
    is_important = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark as important"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['application', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['is_important', '-created_at']),
        ]

    def __str__(self):
        return f"Note on {self.application} by {self.author.email}"

    def save(self, *args, **kwargs):
        """Override save to update application's last_activity_at."""
        super().save(*args, **kwargs)
        
        # Update application's last_activity_at
        self.application.last_activity_at = timezone.now()
        self.application.save(update_fields=['last_activity_at'])