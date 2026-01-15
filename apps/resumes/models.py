import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.validators import FileExtensionValidator
from django.db.models import Q


def resume_upload_path(instance, filename):
    """Generate upload path for resume files."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"resumes/{instance.user.id}/{filename}"


class ResumeManager(models.Manager):
    """Custom manager for Resume model."""

    def for_user(self, user):
        """Get all resumes for a user."""
        return self.filter(user=user)

    def primary_for_user(self, user):
        """Get primary resume for a user."""
        return self.filter(user=user, is_primary=True).first()

    def parsed(self):
        """Get successfully parsed resumes."""
        return self.filter(status='parsed')

    def pending_parse(self):
        """Get resumes that need parsing."""
        return self.filter(status__in=['uploaded', 'failed'])


class Resume(models.Model):
    """Resume model for job seekers."""

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('parsing', 'Parsing'),
        ('parsed', 'Parsed'),
        ('failed', 'Failed'),
    ]

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique UUID for this resume"
    )
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
        help_text="Resume file (PDF or DOCX, max 5MB)",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'txt'])]
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
        default='uploaded',
        db_index=True
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary resume for the user?",
        db_index=True
    )

    # Parsed content
    parsed_text = models.TextField(
        blank=True,
        help_text="Full text extracted from resume"
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="Skills extracted from resume"
    )
    experience_years = models.FloatField(
        null=True,
        blank=True,
        help_text="Years of experience extracted"
    )
    education = models.JSONField(
        default=list,
        blank=True,
        help_text="Education details extracted"
    )
    contact_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contact information extracted"
    )
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="Certifications extracted from resume"
    )

    # Metadata
    uploaded_at = models.DateTimeField(default=timezone.now, db_index=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(
        blank=True,
        help_text="Error message if parsing failed"
    )
    parse_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of parsing attempts"
    )
    last_parse_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time parsing was attempted"
    )

    # Versioning system
    version = models.PositiveIntegerField(
        default=1,
        help_text="Version number of this resume"
    )
    parent_version = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_versions',
        help_text="Parent version this was derived from"
    )
    version_notes = models.TextField(
        blank=True,
        help_text="Notes about what changed in this version"
    )
    is_latest_version = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Is this the latest version in the version chain?"
    )

    # Custom manager
    objects = ResumeManager()

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['user', 'is_primary']),
            models.Index(fields=['status', '-uploaded_at']),
            models.Index(fields=['user', 'is_latest_version']),
            models.Index(fields=['user', 'version']),
        ]
        # FIXED: Remove unique_together constraint that causes issues
        # Instead, enforce in save() method
        constraints = [
            models.CheckConstraint(
                condition=models.Q(file_size__isnull=True) | models.Q(file_size__lte=5242880),  # 5MB in bytes, allow NULL
                name='file_size_limit'
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def save(self, *args, **kwargs):
        """Override save to handle primary resume logic."""
        # Set file size if not set
        if self.file and not self.file_size:
            self.file_size = self.file.size

        # Handle versioning logic
        if not self.pk:  # New resume
            # Find the latest version for this user with the same title
            latest_version = Resume.objects.filter(
                user=self.user,
                title=self.title
            ).order_by('-version').first()
            
            if latest_version:
                # This is a new version of an existing resume
                self.version = latest_version.version + 1
                self.parent_version = latest_version
                # Mark the previous version as not latest
                latest_version.is_latest_version = False
                latest_version.save(update_fields=['is_latest_version'])
            else:
                # This is the first version
                self.version = 1
                self.is_latest_version = True

        # Handle primary resume logic
        if self.is_primary:
            # Ensure only one primary resume per user
            Resume.objects.filter(
                user=self.user, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        else:
            # If this is the only resume, make it primary
            if not self.pk:  # New resume
                if not Resume.objects.filter(user=self.user).exists():
                    self.is_primary = True

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to remove file from storage."""
        # If deleting primary resume, make another one primary
        if self.is_primary:
            next_resume = Resume.objects.filter(
                user=self.user
            ).exclude(pk=self.pk).first()
            if next_resume:
                next_resume.is_primary = True
                next_resume.save(update_fields=['is_primary'])

        # Delete the file from storage
        if self.file:
            if default_storage.exists(self.file.name):
                try:
                    default_storage.delete(self.file.name)
                except Exception as e:
                    # Log error but don't prevent deletion
                    print(f"Error deleting file: {e}")

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

    @property
    def can_reparse(self):
        """Check if resume can be re-parsed."""
        return self.status in ['failed', 'parsed'] and self.file

    @property
    def is_parsing(self):
        """Check if currently parsing."""
        return self.status == 'parsing'

    def get_parsed_skills_list(self):
        """Get skills as a list."""
        if isinstance(self.skills, list):
            return self.skills
        return []

    def get_education_list(self):
        """Get education as a list of dicts."""
        if isinstance(self.education, list):
            return self.education
        return []

    def get_contact_info_dict(self):
        """Get contact info as dict."""
        if isinstance(self.contact_info, dict):
            return self.contact_info
        return {}

    def mark_as_parsing(self):
        """Mark resume as currently being parsed."""
        self.status = 'parsing'
        self.parse_attempts += 1
        self.last_parse_attempt = timezone.now()
        self.save(update_fields=['status', 'parse_attempts', 'last_parse_attempt'])

    def mark_as_parsed(self, parsed_data):
        """Mark resume as successfully parsed."""
        self.status = 'parsed'
        self.parsed_at = timezone.now()
        self.parsed_text = parsed_data.get('text', '')
        self.skills = parsed_data.get('skills', [])
        self.experience_years = parsed_data.get('experience_years')
        self.education = parsed_data.get('education', [])
        self.contact_info = parsed_data.get('contact_info', {})
        self.certifications = parsed_data.get('certifications', [])
        self.error_message = ''
        self.save()

    def mark_as_failed(self, error_message):
        """Mark resume as failed to parse."""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])


class ResumeOptimization(models.Model):
    """Resume optimization analysis results."""
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='optimization')
    
    # Scores (0-100)
    ats_score = models.FloatField(default=0)
    action_verb_score = models.FloatField(default=0)
    quantifiable_score = models.FloatField(default=0)
    formatting_score = models.FloatField(default=0)
    keyword_score = models.FloatField(default=0)
    overall_score = models.FloatField(default=0)
    
    # Analysis data
    action_verb_analysis = models.JSONField(default=dict)
    quantifiable_analysis = models.JSONField(default=dict)
    keyword_analysis = models.JSONField(default=dict)
    formatting_issues = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    
    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-analyzed_at']

    def __str__(self):
        return f"Optimization for {self.resume.title} - Score: {self.overall_score}"


class ResumeSuggestion(models.Model):
    """Auto-generated suggestions for resume improvement."""
    optimization = models.ForeignKey(ResumeOptimization, on_delete=models.CASCADE, related_name='detailed_suggestions')
    
    PRIORITY_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    
    category = models.CharField(max_length=50)  # 'action_verbs', 'formatting', etc
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    title = models.CharField(max_length=200)
    description = models.TextField()
    suggestion = models.TextField()  # Actionable advice
    example_before = models.TextField(blank=True)  # Bad example
    example_after = models.TextField(blank=True)   # Good example
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['priority', 'created_at']
    
    def __str__(self):
        return f"{self.priority.upper()}: {self.title}"