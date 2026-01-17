import uuid
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator

from apps.applications.models import Application


class Interview(models.Model):
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='interviews'
    )
    interview_type = models.CharField(max_length=20, choices=InterviewType.choices)
    status = models.CharField(max_length=20, choices=InterviewStatus.choices, default=InterviewStatus.SCHEDULED)
    scheduled_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    timezone = models.CharField(max_length=50, default='UTC')
    location = models.CharField(max_length=255, blank=True)
    video_link = models.URLField(blank=True, validators=[URLValidator()])
    dial_in_number = models.CharField(max_length=50, blank=True)
    interviewer_name = models.CharField(max_length=255)
    interviewer_email = models.EmailField()
    additional_interviewers = models.JSONField(default=list, blank=True)
    company_notes = models.TextField(blank=True)
    candidate_instructions = models.TextField(blank=True)
    completion_notes = models.TextField(blank=True)
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_1h_sent = models.BooleanField(default=False)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cancelled_interviews'
    )
    cancellation_reason = models.TextField(blank=True)
    original_scheduled_date = models.DateTimeField(null=True, blank=True)
    reschedule_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['scheduled_date']),
        ]

    def __str__(self):
        return f"{self.get_interview_type_display()} - {self.application.applicant.email} - {self.scheduled_date}"

    def get_end_time(self):
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)

    def can_reschedule(self):
        return self.status in {
            self.InterviewStatus.SCHEDULED,
            self.InterviewStatus.RESCHEDULED
        }
