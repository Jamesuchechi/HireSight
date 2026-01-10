from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator, EmailValidator
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, account_type='personal', **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, account_type=account_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('account_type', 'personal')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email authentication and account type."""
    
    ACCOUNT_TYPE_CHOICES = [
        ('personal', 'Personal (Job Seeker)'),
        ('company', 'Company (Recruiter)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        max_length=255,
        unique=True,
        validators=[EmailValidator()],
        help_text='User email address (used for login)'
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default='personal',
        help_text='Type of account: personal (job seeker) or company (recruiter)'
    )
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(
        default=False,
        help_text='Email verification status'
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return full name based on account type."""
        if self.account_type == 'personal' and hasattr(self, 'personal_profile'):
            return self.personal_profile.full_name
        elif self.account_type == 'company' and hasattr(self, 'company_profile'):
            return self.company_profile.company_name
        return self.email
    
    def get_profile(self):
        """Return the appropriate profile based on account type."""
        if self.account_type == 'personal':
            return getattr(self, 'personal_profile', None)
        elif self.account_type == 'company':
            return getattr(self, 'company_profile', None)
        return None


class PersonalProfile(models.Model):
    """Profile for personal (job seeker) accounts."""
    
    PROFILE_VISIBILITY_CHOICES = [
        ('public', 'Public (visible to all)'),
        ('verified_companies', 'Verified Companies Only'),
        ('private', 'Private (hidden)'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('immediate', 'Immediate'),
        ('2_weeks', '2 Weeks Notice'),
        ('1_month', '1 Month Notice'),
        ('not_looking', 'Not Currently Looking'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='personal_profile'
    )
    
    # Basic Info
    full_name = models.CharField(max_length=255)
    headline = models.CharField(
        max_length=255,
        blank=True,
        help_text='Professional headline (e.g., "Senior React Developer")'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True, help_text='Brief professional summary')
    
    # Professional Data (JSON fields for flexibility)
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of skill objects: [{"skill": "React", "proficiency": "expert"}]'
    )
    experience = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of experience objects with company, role, dates, description'
    )
    education = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of education objects with institution, degree, field, dates'
    )
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of certification objects'
    )
    portfolio_links = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of portfolio link objects: [{"type": "github", "url": "..."}]'
    )
    
    # Job Preferences
    preferred_job_types = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of preferred job types: ["full-time", "remote"]'
    )
    salary_expectation_min = models.IntegerField(null=True, blank=True)
    salary_expectation_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='USD')
    availability = models.CharField(
        max_length=50,
        choices=AVAILABILITY_CHOICES,
        default='immediate'
    )
    
    # Settings
    profile_visibility = models.CharField(
        max_length=50,
        choices=PROFILE_VISIBILITY_CHOICES,
        default='public'
    )
    resume_primary_id = models.UUIDField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'personal_profiles'
        verbose_name = 'Personal Profile'
        verbose_name_plural = 'Personal Profiles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['profile_visibility']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.user.email})"
    
    def calculate_completion_score(self):
        """Calculate profile completion percentage (0-100)."""
        score = 0
        total_fields = 10
        
        if self.full_name:
            score += 1
        if self.headline:
            score += 1
        if self.avatar:
            score += 1
        if self.bio:
            score += 1
        if self.skills:
            score += 1
        if self.experience:
            score += 1
        if self.education:
            score += 1
        if self.certifications or self.portfolio_links:
            score += 1
        if self.preferred_job_types:
            score += 1
        if self.resume_primary_id:
            score += 1
        
        return int((score / total_fields) * 100)
    
    def get_top_skills(self, limit=5):
        """Return top N skills."""
        if not self.skills:
            return []
        return [skill.get('skill', '') for skill in self.skills[:limit]]


class CompanyProfile(models.Model):
    """Profile for company (recruiter) accounts."""
    
    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='company_profile'
    )
    
    # Basic Info
    company_name = models.CharField(max_length=255)
    logo = models.ImageField(
        upload_to='company_logos/',
        null=True,
        blank=True
    )
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(
        max_length=50,
        choices=COMPANY_SIZE_CHOICES,
        blank=True
    )
    
    # Company Details
    locations = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of location objects: [{"city": "SF", "state": "CA", "country": "USA", "is_hq": true}]'
    )
    website = models.URLField(max_length=512, blank=True)
    description = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    culture = models.TextField(blank=True)
    
    # Benefits & Perks
    benefits = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of benefits: ["Health Insurance", "Remote Work", "401k"]'
    )
    team_photos = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of team photo objects: [{"url": "...", "caption": "Our amazing team"}]'
    )
    
    # Additional Info
    founded_year = models.IntegerField(null=True, blank=True)
    
    # Verification
    verification_status = models.CharField(
        max_length=50,
        choices=VERIFICATION_STATUS_CHOICES,
        default='unverified'
    )
    verification_docs = models.FileField(
        upload_to='verification_docs/',
        null=True,
        blank=True,
        help_text='Business registration or tax documents'
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'company_profiles'
        verbose_name = 'Company Profile'
        verbose_name_plural = 'Company Profiles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['company_name']),
        ]
    
    def __str__(self):
        return f"{self.company_name} ({self.user.email})"
    
    def is_verified(self):
        """Check if company is verified."""
        return self.verification_status == 'verified'
    
    def get_hq_location(self):
        """Return headquarters location."""
        if not self.locations:
            return None
        for location in self.locations:
            if location.get('is_hq', False):
                return f"{location.get('city', '')}, {location.get('state', '')}"
        return None


class EmailVerificationToken(models.Model):
    """Token for email verification."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'email_verification_tokens'
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token for {self.user.email}"
    
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at


class PasswordResetToken(models.Model):
    """Token for password reset."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at