from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator, EmailValidator
import uuid
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.db.models.signals import post_save
from django.dispatch import receiver
import secrets


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
        extra_fields.setdefault('email_verified', True)
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
    
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text='Whether two-factor authentication is enabled'
    )
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(
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
            models.Index(fields=['email_verified']),
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

    def get_display_name(self):
        """User-facing label used when referencing the user."""
        full_name = self.get_full_name()
        return full_name if full_name else self.email
    
    def get_profile(self):
        """Return the appropriate profile based on account type."""
        if self.account_type == 'personal':
            return getattr(self, 'personal_profile', None)
        elif self.account_type == 'company':
            return getattr(self, 'company_profile', None)
        return None
    
    def has_2fa_enabled(self):
        """Check if user has 2FA enabled and configured."""
        try:
            from django_otp.plugins.otp_totp.models import TOTPDevice
            return self.two_factor_enabled and TOTPDevice.objects.filter(
                user=self,
                confirmed=True
            ).exists()
        except ImportError:
            # If django-otp not installed, return False
            return False
    
    def get_active_sessions_count(self):
        """Get count of active sessions."""
        return self.user_sessions.filter(
            expires_at__gte=timezone.now()
        ).count()
    
    def get_profile_views_count(self, days=None):
        """Get count of profile views."""
        views = self.profile_views_received.all()
        if days:
            views = views.filter(
                viewed_at__gte=timezone.now() - timezone.timedelta(days=days)
            )
        return views.count()

class PersonalProfile(models.Model):
    """Profile for personal (job seeker) accounts."""
    
    PROFILE_VISIBILITY_CHOICES = [
        ('public', 'Public (visible to all)'),
        ('verified_companies', 'Verified Companies Only'),
        ('private', 'Private (hidden)'),
    ]
    
    REMOTE_PREFERENCE_CHOICES = [
        ('remote', 'Fully Remote'),
        ('hybrid', 'Hybrid (Remote + Office)'),
        ('on-site', 'On-site Only'),
        ('no_preference', 'No Preference'),
    ]

    AVAILABILITY_CHOICES = [
        ('immediate', 'Immediate'),
        ('2_weeks', '2 Weeks Notice'),
        ('1_month', '1 Month Notice'),
        ('not_looking', 'Not Currently Looking'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('NGN', 'NGN - Nigerian Naira'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('AUD', 'AUD - Australian Dollar'),
        ('JPY', 'JPY - Japanese Yen'),
        ('CNY', 'CNY - Chinese Yuan'),
        ('INR', 'INR - Indian Rupee'),
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
    remote_preference = models.CharField(
        max_length=50,
        choices=REMOTE_PREFERENCE_CHOICES,
        default='no_preference',
        help_text='Preferred work location type'
    )
    salary_expectation_min = models.IntegerField(null=True, blank=True)
    salary_expectation_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='USD',
        blank=True
    )
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
        """Calculate weighted profile completion percentage (0-100).
        
        Weights are assigned based on importance:
        - Basic info (name, headline, avatar, bio): 15% total
        - Skills: 25% (most important for job matching)
        - Experience: 20% (critical for employability)
        - Education: 15% (important but less than experience)
        - Certifications: 10% (valuable but optional)
        - Portfolio: 10% (showcase of work)
        - Job preferences: 5% (helps with job matching)
        """
        
        # Initialize total score and weights
        total_score = 0.0
        
        # 1. Basic Information (15% total)
        basic_info_weight = 15.0
        basic_info_fields = 4  # full_name, headline, avatar, bio
        basic_info_score = 0
        
        if self.full_name:
            basic_info_score += 1
        if self.headline:
            basic_info_score += 1
        if self.avatar:
            basic_info_score += 1
        if self.bio:
            basic_info_score += 1
        
        # Calculate basic info contribution (max 15%)
        if basic_info_fields > 0:
            basic_info_percentage = (basic_info_score / basic_info_fields) * basic_info_weight
            total_score += basic_info_percentage
        
        # 2. Skills (25% total) - weighted by number of skills and proficiency
        skills_weight = 25.0
        if self.skills and len(self.skills) > 0:
            # Calculate quality score based on proficiency
            proficiency_scores = {
                'beginner': 0.5,
                'intermediate': 0.8,
                'advanced': 1.0,
                'expert': 1.2
            }
            
            total_skill_score = 0.0
            for skill in self.skills:
                proficiency = skill.get('proficiency', 'intermediate').lower()
                total_skill_score += proficiency_scores.get(proficiency, 0.8)
            
            # Normalize by number of skills and cap at max weight
            avg_skill_quality = total_skill_score / len(self.skills)
            skills_percentage = min(avg_skill_quality * skills_weight, skills_weight)
            total_score += skills_percentage
        
        # 3. Experience (20% total) - weighted by number of experiences and duration
        experience_weight = 20.0
        if self.experience and len(self.experience) > 0:
            # Calculate experience quality score
            experience_quality = min(len(self.experience) * 2.5, 10)  # Max 10 points for 4+ experiences
            
            # Check for current positions (more valuable)
            has_current = any(exp.get('current', False) for exp in self.experience)
            if has_current:
                experience_quality += 2
            
            # Calculate percentage (max 20%)
            experience_percentage = min((experience_quality / 10) * experience_weight, experience_weight)
            total_score += experience_percentage
        
        # 4. Education (15% total)
        education_weight = 15.0
        if self.education and len(self.education) > 0:
            # Calculate education quality score
            education_quality = len(self.education) * 2  # 2 points per education entry
            
            # Check for completed degrees (have end_year)
            completed_degrees = sum(1 for edu in self.education if edu.get('end_year'))
            education_quality += completed_degrees
            
            # Calculate percentage (max 15%)
            education_percentage = min((education_quality / 5) * education_weight, education_weight)
            total_score += education_percentage
        
        # 5. Certifications (10% total)
        certifications_weight = 10.0
        if self.certifications and len(self.certifications) > 0:
            # Calculate certification quality score
            cert_quality = len(self.certifications) * 1.5  # 1.5 points per certification
            
            # Check for verified certifications (have URL)
            verified_certs = sum(1 for cert in self.certifications if cert.get('url'))
            cert_quality += verified_certs * 0.5
            
            # Calculate percentage (max 10%)
            cert_percentage = min((cert_quality / 3) * certifications_weight, certifications_weight)
            total_score += cert_percentage
        
        # 6. Portfolio Links (10% total)
        portfolio_weight = 10.0
        if self.portfolio_links and len(self.portfolio_links) > 0:
            # Calculate portfolio quality score
            portfolio_quality = len(self.portfolio_links) * 2  # 2 points per link
            
            # Check for diverse portfolio (different types)
            link_types = set(link.get('type', 'website') for link in self.portfolio_links)
            portfolio_quality += len(link_types)
            
            # Calculate percentage (max 10%)
            portfolio_percentage = min((portfolio_quality / 4) * portfolio_weight, portfolio_weight)
            total_score += portfolio_percentage
        
        # 7. Job Preferences (5% total)
        job_prefs_weight = 5.0
        job_prefs_score = 0
        
        if self.preferred_job_types and len(self.preferred_job_types) > 0:
            job_prefs_score += 1
        if self.remote_preference and self.remote_preference != 'no_preference':
            job_prefs_score += 1
        if self.salary_expectation_min or self.salary_expectation_max:
            job_prefs_score += 1
        if self.availability and self.availability != 'not_looking':
            job_prefs_score += 1
        
        # Calculate job preferences percentage (max 5%)
        if job_prefs_score > 0:
            job_prefs_percentage = (job_prefs_score / 4) * job_prefs_weight
            total_score += job_prefs_percentage
        
        # Cap at 100% and return as integer
        final_score = min(round(total_score), 100)
        return int(final_score)
    
    def get_top_skills(self, limit=5):
        """Return top N skills."""
        if not self.skills:
            return []
        return [skill.get('skill', '') for skill in self.skills[:limit]]

    @property
    def top_skills(self):
        """Return top skills for templates."""
        return self.get_top_skills()

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
        help_text='Array of location objects: [{"address": "123 Main St", "city": "SF", "state": "CA", "country": "USA", "is_hq": true, "lat": 37.7749, "lng": -122.4194}]'
    )
    website = models.URLField(max_length=512, blank=True)
    linkedin = models.URLField(max_length=512, blank=True)
    twitter = models.URLField(max_length=512, blank=True)
    facebook = models.URLField(max_length=512, blank=True)
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
                parts = []
                if location.get('address'):
                    parts.append(location.get('address'))
                if location.get('city'):
                    parts.append(location.get('city'))
                if location.get('state'):
                    parts.append(location.get('state'))
                if location.get('country'):
                    parts.append(location.get('country'))
                return ', '.join(parts) if parts else None
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


class EmailPreferences(models.Model):
    """Email notification preferences for users."""
    
    EMAIL_FREQUENCY_CHOICES = [
        ('instant', 'Instant (real-time notifications)'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('off', 'Off (in-app only)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_preferences'
    )
    
    # Global frequency setting
    email_frequency = models.CharField(
        max_length=20,
        choices=EMAIL_FREQUENCY_CHOICES,
        default='instant',
        help_text='Default email notification frequency'
    )
    
    # Notification type preferences (for personal accounts)
    notify_new_application = models.BooleanField(
        default=True,
        help_text='New job recommendations'
    )
    notify_application_status_changed = models.BooleanField(
        default=True,
        help_text='When an application status changes'
    )
    notify_new_message = models.BooleanField(
        default=True,
        help_text='When someone sends you a message'
    )
    notify_profile_viewed = models.BooleanField(
        default=True,
        help_text='When someone views your profile'
    )
    notify_new_follower = models.BooleanField(
        default=True,
        help_text='When someone follows you'
    )
    notify_followed_company_job = models.BooleanField(
        default=True,
        help_text='New jobs from companies you follow'
    )
    notify_interview_scheduled = models.BooleanField(
        default=True,
        help_text='Interview invitations and schedule changes'
    )
    notify_job_recommendations = models.BooleanField(
        default=True,
        help_text='Weekly/daily job recommendations'
    )
    
    # Notification type preferences (for company accounts)
    notify_new_applicant = models.BooleanField(
        default=True,
        help_text='New applications received'
    )
    notify_screening_complete = models.BooleanField(
        default=True,
        help_text='Resume screening completed'
    )
    notify_job_expiring_soon = models.BooleanField(
        default=True,
        help_text='Reminders for jobs about to expire'
    )
    notify_applicant_response = models.BooleanField(
        default=True,
        help_text='When applicants respond to messages'
    )
    notify_new_company_follower = models.BooleanField(
        default=True,
        help_text='When someone follows your company'
    )
    
    # Other preferences
    unsubscribe_token = models.CharField(
        max_length=255,
        unique=True,
        default=None,
        null=True,
        blank=True,
        help_text='Token for email unsubscribe links'
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_digest_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'email_preferences'
        verbose_name = 'Email Preferences'
        verbose_name_plural = 'Email Preferences'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['unsubscribe_token']),
        ]
    
    def __str__(self):
        return f"Email preferences for {self.user.email}"
    
    def get_enabled_notifications(self):
        """Return list of enabled notification types based on user type."""
        enabled = []
        
        if self.user.account_type == 'personal':
            if self.notify_new_application:
                enabled.append('new_application')
            if self.notify_application_status_changed:
                enabled.append('application_status_changed')
            if self.notify_new_message:
                enabled.append('new_message')
            if self.notify_profile_viewed:
                enabled.append('profile_viewed')
            if self.notify_new_follower:
                enabled.append('new_follower')
            if self.notify_followed_company_job:
                enabled.append('followed_company_job')
            if self.notify_interview_scheduled:
                enabled.append('interview_scheduled')
            if self.notify_job_recommendations:
                enabled.append('job_recommendations')
        else:  # company
            if self.notify_new_applicant:
                enabled.append('new_applicant')
            if self.notify_screening_complete:
                enabled.append('screening_complete')
            if self.notify_job_expiring_soon:
                enabled.append('job_expiring_soon')
            if self.notify_applicant_response:
                enabled.append('applicant_response')
            if self.notify_new_company_follower:
                enabled.append('new_company_follower')
        
        return enabled
    
    def should_send_notification(self, notification_type):
        """Check if notification should be sent based on preferences."""
        enabled = self.get_enabled_notifications()
        return notification_type in enabled


class EmailChangeToken(models.Model):
    """Token for email change verification."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_change_tokens')
    new_email = models.EmailField(help_text='The new email address to change to')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'email_change_tokens'
        verbose_name = 'Email Change Token'
        verbose_name_plural = 'Email Change Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Email change token for {self.user.email} -> {self.new_email}"
    
    def is_expired(self):
        """Check if token has expired."""
        return timezone.now() > self.expires_at
    



class APIKey(models.Model):
    """API keys for programmatic access to the platform."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_keys',
        help_text='User who owns this API key'
    )
    name = models.CharField(
        max_length=255,
        help_text='Descriptive name for this API key'
    )
    key = models.CharField(
        max_length=64,
        unique=True,
        help_text='The actual API key string'
    )
    key_prefix = models.CharField(
        max_length=8,
        help_text='First 8 characters of the key for display purposes'
    )
    created_at = models.DateTimeField(default=timezone.now)
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time this key was used'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this key is currently active'
    )
    
    class Meta:
        db_table = 'api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"
    
    @classmethod
    def generate_key(cls):
        """Generate a new secure API key."""
        return f"hs_{secrets.token_urlsafe(48)}"
    
    def save(self, *args, **kwargs):
        """Set key_prefix on creation."""
        if not self.key_prefix and self.key:
            self.key_prefix = self.key[:8]
        super().save(*args, **kwargs)
    
    def record_usage(self):
        """Update last_used_at timestamp."""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class ProfileView(models.Model):
    """Track when users view profiles for analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='profile_views_received',
        help_text='User whose profile was viewed'
    )
    viewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile_views_made',
        help_text='User who viewed the profile (null if anonymous)'
    )
    viewer_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of anonymous viewers'
    )
    viewer_user_agent = models.TextField(
        blank=True,
        help_text='Browser/device information'
    )
    viewed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'profile_views'
        verbose_name = 'Profile View'
        verbose_name_plural = 'Profile Views'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['profile_user', '-viewed_at']),
            models.Index(fields=['viewer', '-viewed_at']),
        ]
    
    def __str__(self):
        viewer_name = self.viewer.get_full_name() if self.viewer else f"Anonymous ({self.viewer_ip})"
        return f"{viewer_name} viewed {self.profile_user.get_full_name()} at {self.viewed_at}"


class UserSession(models.Model):
    """Track active user sessions for session management."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_sessions'
    )
    session_key = models.CharField(
        max_length=40,
        unique=True,
        help_text='Django session key'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the session'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='Browser/device information'
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text='Approximate location (city, country)'
    )
    device_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Device type (desktop, mobile, tablet)'
    )
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(help_text='When this session expires')
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type} - {self.ip_address}"
    
    def is_expired(self):
        """Check if session has expired."""
        return timezone.now() > self.expires_at
    
    def is_current(self, request):
        """Check if this is the current session."""
        return self.session_key == request.session.session_key
    
    def get_location_display(self):
        """Get formatted location string."""
        return self.location if self.location else "Unknown location"
    
    def get_device_display(self):
        """Get formatted device string."""
        if self.device_type:
            return self.device_type.capitalize()
        return "Unknown device"


class AccountDeletionLog(models.Model):
    """Log account deletions for audit and analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_email = models.EmailField(help_text='Email of deleted account')
    account_type = models.CharField(
        max_length=20,
        help_text='Account type (personal/company)'
    )
    deletion_reason = models.TextField(
        blank=True,
        help_text='Optional reason for deletion'
    )
    deleted_at = models.DateTimeField(default=timezone.now)
    deleted_by_user = models.BooleanField(
        default=True,
        help_text='True if user deleted their own account'
    )
    
    # Store some anonymized stats
    account_age_days = models.IntegerField(
        null=True,
        blank=True,
        help_text='How many days the account existed'
    )
    total_applications = models.IntegerField(
        default=0,
        help_text='Number of applications made (if personal)'
    )
    total_job_posts = models.IntegerField(
        default=0,
        help_text='Number of jobs posted (if company)'
    )
    
    class Meta:
        db_table = 'account_deletion_logs'
        verbose_name = 'Account Deletion Log'
        verbose_name_plural = 'Account Deletion Logs'
        ordering = ['-deleted_at']
        indexes = [
            models.Index(fields=['deleted_at']),
            models.Index(fields=['account_type']),
        ]
    
    def __str__(self):
        return f"{self.user_email} deleted on {self.deleted_at.strftime('%Y-%m-%d')}"


class UserProfile(models.Model):
    """Reusable profile storing contact details for resumes."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='Generic profile used for resume headers and contact info'
    )
    full_name = models.CharField(
        max_length=200,
        help_text='Your full name as it should appear on resumes'
    )
    professional_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Current or target job title (e.g., "Senior Software Engineer")'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary phone number'
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Location (city, region, or country)'
    )
    linkedin_url = models.URLField(
        blank=True,
        help_text='LinkedIn profile URL'
    )
    portfolio_url = models.URLField(
        blank=True,
        help_text='Portfolio or personal website'
    )
    github_url = models.URLField(
        blank=True,
        help_text='GitHub profile URL (for technical roles)'
    )
    practice_enabled = models.BooleanField(
        default=True,
        help_text='Allow the user to create interview practice sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.full_name}'s Profile"

    def get_header_text(self):
        """Generate formatted header text for AI rewrites and resume previews."""
        lines = [self.full_name]
        if self.professional_title:
            lines.append(self.professional_title)

        contact_parts = []
        if self.location:
            contact_parts.append(self.location)
        if self.phone:
            contact_parts.append(self.phone)
        if self.user.email:
            contact_parts.append(self.user.email)
        if self.linkedin_url:
            contact_parts.append(self.linkedin_url)
        if self.portfolio_url:
            contact_parts.append(self.portfolio_url)
        if self.github_url:
            contact_parts.append(self.github_url)

        if contact_parts:
            lines.append(" | ".join(contact_parts))

        return "\n".join(lines)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a user profile when a new user is created."""
    if created:
        UserProfile.objects.create(
            user=instance,
            full_name=instance.get_full_name() or instance.email.split('@')[0]
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure the user profile stays in sync when the user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
