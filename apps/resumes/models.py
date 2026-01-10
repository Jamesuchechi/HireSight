import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage


def resume_upload_path(instance, filename):
    """Generate upload path for resume files."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"resumes/{instance.user.id}/{filename}"


class Resume(models.Model):
    """Resume model for job seekers."""

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('parsing', 'Parsing'),
        ('parsed', 'Parsed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    title = models.CharField(
        max_length=200,
        help_text="Resume title (e.g., 'Software Engineer Resume')"
    )
    file = models.FileField(
        upload_to=resume_upload_path,
        help_text="Resume file (PDF or DOCX, max 5MB)"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes",
        null=True,
        blank=True
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="Original filename before upload"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded'
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary resume for the user?"
    )

    # Parsed content
    parsed_text = models.TextField(
        blank=True,
        help_text="Full text extracted from resume"
    )
    skills = models.JSONField(
        default=list,
        help_text="Skills extracted from resume"
    )
    experience_years = models.FloatField(
        null=True,
        blank=True,
        help_text="Years of experience extracted"
    )
    education = models.JSONField(
        default=list,
        help_text="Education details extracted"
    )
    contact_info = models.JSONField(
        default=dict,
        help_text="Contact information extracted"
    )

    # Metadata
    uploaded_at = models.DateTimeField(default=timezone.now)
    parsed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(
        blank=True,
        help_text="Error message if parsing failed"
    )

    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ['user', 'is_primary']  # Only one primary per user

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def save(self, *args, **kwargs):
        """Override save to handle primary resume logic."""
        if self.is_primary:
            # Ensure only one primary resume per user
            Resume.objects.filter(user=self.user, is_primary=True).update(is_primary=False)

        # Set file size if not set
        if self.file and not self.file_size:
            self.file_size = self.file.size

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to remove file from storage."""
        if self.file:
            # Delete the file from storage
            if default_storage.exists(self.file.name):
                default_storage.delete(self.file.name)
        super().delete(*args, **kwargs)

    @property
    def file_extension(self):
        """Get file extension."""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''

    @property
    def is_pdf(self):
        """Check if file is PDF."""
        return self.file_extension == '.pdf'

    @property
    def is_docx(self):
        """Check if file is DOCX."""
        return self.file_extension == '.docx'

    def get_parsed_skills_list(self):
        """Get skills as a list."""
        return self.skills if isinstance(self.skills, list) else []

    def get_education_list(self):
        """Get education as a list of dicts."""
        return self.education if isinstance(self.education, list) else []