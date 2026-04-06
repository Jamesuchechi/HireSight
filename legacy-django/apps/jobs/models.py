import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, Count, Avg
import bleach
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable


class JobStatus(models.TextChoices):
    """Job status choices."""
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    CLOSED = 'closed', 'Closed'
    ARCHIVED = 'archived', 'Archived'


class RemoteType(models.TextChoices):
    """Remote work type choices."""
    ONSITE = 'onsite', 'On-site'
    REMOTE = 'remote', 'Fully Remote'
    HYBRID = 'hybrid', 'Hybrid'


class EmploymentType(models.TextChoices):
    """Employment type choices."""
    FULL_TIME = 'full_time', 'Full-time'
    PART_TIME = 'part_time', 'Part-time'
    CONTRACT = 'contract', 'Contract'
    FREELANCE = 'freelance', 'Freelance'
    INTERNSHIP = 'internship', 'Internship'


class ExperienceLevel(models.TextChoices):
    """Experience level choices."""
    ENTRY = 'entry', 'Entry Level'
    MID = 'mid', 'Mid Level'
    SENIOR = 'senior', 'Senior Level'
    LEAD = 'lead', 'Lead/Principal'
    EXECUTIVE = 'executive', 'Executive'


class SalaryPeriod(models.TextChoices):
    """Salary period choices."""
    HOURLY = 'hourly', 'Per Hour'
    MONTHLY = 'monthly', 'Per Month'
    YEARLY = 'yearly', 'Per Year'


class JobManager(models.Manager):
    """Custom manager for Job model."""

    def active(self):
        """Get all active jobs."""
        return self.filter(status=JobStatus.ACTIVE)

    def for_company(self, company):
        """Get jobs for a specific company."""
        return self.filter(company=company)

    def recent(self, days=7):
        """Get jobs posted in the last N days."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)

    def featured(self):
        """Get featured jobs."""
        return self.filter(is_featured=True, status=JobStatus.ACTIVE)

    def search(self, query):
        """Search jobs by keyword."""
        return self.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__company_name__icontains=query)
        )

    def with_application_count(self):
        """Annotate with application count."""
        return self.annotate(app_count=Count('applications'))


class Job(models.Model):
    """Job posting model."""

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Company
    company = models.ForeignKey(
        'accounts.CompanyProfile',
        on_delete=models.CASCADE,
        related_name='jobs'
    )

    # Basic Info
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Job title"
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        db_index=True,
        help_text="URL-friendly job identifier"
    )

    # Description
    description = models.TextField(
        help_text="Detailed job description"
    )
    responsibilities = models.TextField(
        blank=True,
        help_text="Key responsibilities"
    )
    requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Job requirements (skills, experience, education)"
    )
    nice_to_have = models.TextField(
        blank=True,
        help_text="Nice-to-have qualifications"
    )
    benefits = models.TextField(
        blank=True,
        help_text="Benefits and perks"
    )

    # Location
    location = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Job location (city, state, country)"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate for location"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate for location"
    )
    is_remote = models.BooleanField(
        default=False,
        help_text="Is this a remote position?"
    )
    remote_type = models.CharField(
        max_length=20,
        choices=RemoteType.choices,
        default=RemoteType.ONSITE,
        help_text="Remote work type"
    )
    timezone_preference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Preferred timezone (if remote)"
    )

    # Employment Details
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
        help_text="Type of employment"
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID,
        help_text="Required experience level"
    )

    # Salary
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum salary"
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum salary"
    )
    salary_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency code (e.g., USD, EUR)"
    )
    salary_period = models.CharField(
        max_length=20,
        choices=SalaryPeriod.choices,
        default=SalaryPeriod.YEARLY,
        help_text="Salary payment period"
    )

    # Status & Visibility
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.DRAFT,
        db_index=True,
        help_text="Job posting status"
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Feature this job (premium)"
    )
    positions_available = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of positions available"
    )
    application_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Application deadline"
    )

    # Department
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department or team for this position"
    )

    # Application Settings
    requires_cover_letter = models.BooleanField(
        default=False,
        help_text="Require cover letter?"
    )
    requires_portfolio = models.BooleanField(
        default=False,
        help_text="Require portfolio?"
    )
    screening_questions = models.JSONField(
        default=list,
        blank=True,
        help_text="Custom screening questions"
    )
    application_email = models.EmailField(
        blank=True,
        help_text="Email for applications (optional)"
    )

    # Education Requirements
    education_required = models.CharField(
        max_length=100,
        blank=True,
        help_text="Minimum education requirement"
    )

    # Tags for skills and keywords
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Skills, keywords, and tags for this job"
    )

    # Analytics
    views_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of views"
    )
    applications_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of applications"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When job was published"
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When job was closed"
    )

    # Custom manager
    objects = JobManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['location', 'status']),
            models.Index(fields=['employment_type', 'status']),
            models.Index(fields=['experience_level', 'status']),
            models.Index(fields=['is_featured', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                name='salary_max_gte_min',
                condition=Q(salary_max__gte=models.F('salary_min')) | Q(salary_max__isnull=True)
            ),
        ]

    def __str__(self):
        return f"{self.title} at {self.company.company_name}"

    def save(self, *args, **kwargs):
        """Override save to generate slug and handle publishing."""
        # Generate unique slug
        if not self.slug:
            self.slug = self.generate_unique_slug()

        # Sanitize HTML in description
        if self.description:
            # Allow common HTML tags and attributes for rich text
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img', 'div', 'span'
            ]
            allowed_attributes = {
                'a': ['href', 'title', 'target'],
                'img': ['src', 'alt', 'title', 'width', 'height'],
                'div': ['class'],
                'span': ['class'],
                '*': ['style']
            }
            self.description = bleach.clean(
                self.description,
                tags=allowed_tags,
                attributes=allowed_attributes,
                strip=True
            )

        # Set published_at when changing to active
        if self.status == JobStatus.ACTIVE and not self.published_at:
            self.published_at = timezone.now()

        # Set closed_at when closing
        if self.status == JobStatus.CLOSED and not self.closed_at:
            self.closed_at = timezone.now()

        # Geocode location if it has changed and is not remote
        if not self.is_remote and self.location:
            # For new jobs or when location has changed
            if self.pk is None:
                self.geocode_location()
            else:
                try:
                    old_job = Job.objects.get(pk=self.pk)
                    if old_job.location != self.location:
                        self.geocode_location()
                except Job.DoesNotExist:
                    self.geocode_location()

        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        """Generate unique slug from title."""
        base_slug = slugify(self.title)[:200]
        slug = base_slug
        counter = 1

        while Job.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def get_absolute_url(self):
        """Get job detail URL."""
        return reverse('jobs:detail', kwargs={'slug': self.slug})

    @property
    def is_active(self):
        """Check if job is active."""
        return self.status == JobStatus.ACTIVE

    @property
    def is_expired(self):
        """Check if job has expired."""
        if self.application_deadline:
            return timezone.now() > self.application_deadline
        return False

    @property
    def days_since_posted(self):
        """Get days since job was posted."""
        if self.published_at:
            delta = timezone.now() - self.published_at
            return delta.days
        return None

    @property
    def application_rate(self):
        """Calculate application conversion rate."""
        if self.views_count > 0:
            return (self.applications_count / self.views_count) * 100
        return 0

    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_applications(self):
        """Increment application count."""
        self.applications_count += 1
        self.save(update_fields=['applications_count'])

    def geocode_location(self):
        """Geocode the location to get latitude and longitude."""
        if not self.location:
            return

        try:
            geolocator = Nominatim(user_agent="hiresight-job-geocoding")
            location = geolocator.geocode(self.location, timeout=10)

            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
            else:
                # If geocoding fails, clear coordinates
                self.latitude = None
                self.longitude = None

        except (GeocoderTimedOut, GeocoderUnavailable):
            # If geocoding service is unavailable, don't update coordinates
            pass
        except Exception:
            # For any other error, clear coordinates
            self.latitude = None
            self.longitude = None

    def distance_to(self, latitude, longitude):
        """Calculate distance in miles to given coordinates."""
        if not (self.latitude and self.longitude and latitude and longitude):
            return None

        # Haversine formula for distance calculation
        import math

        # Convert to radians
        lat1_rad = math.radians(float(self.latitude))
        lon1_rad = math.radians(float(self.longitude))
        lat2_rad = math.radians(float(latitude))
        lon2_rad = math.radians(float(longitude))

        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        # Earth's radius in miles
        radius = 3959
        distance = radius * c

        return distance

    def get_salary_display(self):
        """Get formatted salary range."""
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,.0f} - ${self.salary_max:,.0f}"
        elif self.salary_min:
            return f"${self.salary_min:,.0f}+"
        return "Not specified"

    def get_requirements_list(self):
        """Return requirements as a flat list of strings for display."""
        requirements = []

        data = self.requirements
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    for entry in value:
                        text = str(entry).strip()
                        if text:
                            requirements.append(text)
                elif isinstance(value, str):
                    text = value.strip()
                    if text:
                        requirements.append(text)
        elif isinstance(data, list):
            for entry in data:
                text = str(entry).strip()
                if text:
                    requirements.append(text)
        elif isinstance(data, str):
            text = data.strip()
            if text:
                requirements.append(text)

        return requirements

    def is_saved_by(self, user):
        """Check if job is saved by user."""
        if user.is_authenticated:
            return self.saved_by.filter(user=user).exists()
        return False


class SavedJob(models.Model):
    """Model for users saving/bookmarking jobs."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_jobs'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        help_text="Personal notes about this job"
    )

    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['user', '-saved_at']),
        ]

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"


class JobView(models.Model):
    """Track job views for analytics."""

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_views'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    referrer = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['job', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
        ]

    def __str__(self):
        return f"View of {self.job.title} at {self.viewed_at}"
