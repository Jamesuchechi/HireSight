"""
Analytics models for tracking user activity and generating insights.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import JSONField

User = get_user_model()


class ProfileView(models.Model):
    """Track profile views for job seekers."""
    
    profile_owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_profile_views_received'
    )
    viewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_profile_views_made'
    )
    viewer_ip = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['profile_owner', '-viewed_at']),
        ]
    
    def __str__(self):
        viewer_name = self.viewer.email if self.viewer else f"Anonymous ({self.viewer_ip})"
        return f"{viewer_name} viewed {self.profile_owner.email}'s profile"


class JobView(models.Model):
    """Track job listing views."""
    
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='analytics_views'
    )
    viewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs_viewed'
    )
    viewer_ip = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    referrer = models.URLField(max_length=500, blank=True, null=True)
    
    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['job', '-viewed_at']),
        ]
    
    def __str__(self):
        viewer_name = self.viewer.email if self.viewer else f"Anonymous ({self.viewer_ip})"
        return f"{viewer_name} viewed job: {self.job.title}"


class SearchQuery(models.Model):
    """Track search queries for analytics and improvement."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_queries'
    )
    query_text = models.CharField(max_length=500)
    filters = JSONField(default=dict, blank=True)
    results_count = models.IntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-searched_at']
        verbose_name_plural = 'Search queries'
    
    def __str__(self):
        return f"{self.query_text} ({self.results_count} results)"


class ApplicationAnalytics(models.Model):
    """Aggregate metrics for applications - updated daily via task."""
    
    date = models.DateField(unique=True, db_index=True)
    total_applications = models.IntegerField(default=0)
    applications_pending = models.IntegerField(default=0)
    applications_screening = models.IntegerField(default=0)
    applications_interview = models.IntegerField(default=0)
    applications_offer = models.IntegerField(default=0)
    applications_hired = models.IntegerField(default=0)
    applications_rejected = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Application analytics'
    
    def __str__(self):
        return f"Analytics for {self.date}"


class ApplicationMetrics(models.Model):
    """Aggregate metrics for applications - updated daily via task."""
    
    date = models.DateField(unique=True, db_index=True)
    total_applications = models.IntegerField(default=0)
    applications_pending = models.IntegerField(default=0)
    applications_screening = models.IntegerField(default=0)
    applications_interview = models.IntegerField(default=0)
    applications_offer = models.IntegerField(default=0)
    applications_hired = models.IntegerField(default=0)
    applications_rejected = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Application metrics'
    
    def __str__(self):
        return f"Metrics for {self.date}"


class UserActivityLog(models.Model):
    """Log significant user actions for analytics."""
    
    ACTION_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('profile_update', 'Profile Update'),
        ('resume_upload', 'Resume Upload'),
        ('job_post', 'Job Post'),
        ('job_apply', 'Job Apply'),
        ('message_sent', 'Message Sent'),
        ('follow', 'Follow'),
        ('unfollow', 'Unfollow'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    metadata = JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_action_type_display()} at {self.timestamp}"


class CompanyAnalyticsSnapshot(models.Model):
    """Daily snapshot of company analytics."""
    
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_snapshots',
        limit_choices_to={'account_type': 'company'}
    )
    date = models.DateField(db_index=True)
    
    # Job metrics
    total_jobs = models.IntegerField(default=0)
    active_jobs = models.IntegerField(default=0)
    closed_jobs = models.IntegerField(default=0)
    
    # Application metrics
    total_applications = models.IntegerField(default=0)
    new_applications_today = models.IntegerField(default=0)
    pending_review = models.IntegerField(default=0)
    
    # Hiring metrics
    total_hires = models.IntegerField(default=0)
    avg_time_to_hire = models.FloatField(null=True, blank=True)  # in days
    
    # Engagement metrics
    total_job_views = models.IntegerField(default=0)
    followers_count = models.IntegerField(default=0)
    cost_per_hire = models.FloatField(null=True, blank=True)
    applications_by_source = JSONField(default=dict, blank=True)
    resumes_screened = models.IntegerField(default=0)
    top_skills = JSONField(default=list, blank=True)
    skill_gaps = JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['company', 'date']
        indexes = [
            models.Index(fields=['company', '-date']),
        ]
    
    def __str__(self):
        return f"{self.company.email} snapshot for {self.date}"


class PersonalAnalyticsSnapshot(models.Model):
    """Daily snapshot of personal user analytics."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='personal_analytics_snapshots',
        limit_choices_to={'account_type': 'personal'}
    )
    date = models.DateField(db_index=True)
    
    # Application metrics
    total_applications = models.IntegerField(default=0)
    applications_pending = models.IntegerField(default=0)
    applications_screening = models.IntegerField(default=0)
    applications_interview = models.IntegerField(default=0)
    applications_offer = models.IntegerField(default=0)
    applications_hired = models.IntegerField(default=0)
    applications_rejected = models.IntegerField(default=0)
    
    # Engagement metrics
    profile_views_count = models.IntegerField(default=0)
    jobs_viewed_count = models.IntegerField(default=0)
    jobs_saved_count = models.IntegerField(default=0)
    searches_performed = models.IntegerField(default=0)
    
    # Success metrics
    avg_match_score = models.FloatField(null=True, blank=True)
    response_rate = models.FloatField(null=True, blank=True)  # percentage
    skill_assessments_taken = models.IntegerField(default=0)
    avg_skill_assessment_score = models.FloatField(null=True, blank=True)
    badges_earned = JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} snapshot for {self.date}"


class SkillAssessmentResult(models.Model):
    """Record skill assessment results for personal users."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skill_assessments',
        limit_choices_to={'account_type': 'personal'}
    )
    test_name = models.CharField(max_length=200)
    score = models.FloatField()
    max_score = models.FloatField(default=100.0)
    passed = models.BooleanField(default=False)
    badge_awarded = models.CharField(max_length=100, blank=True, null=True)
    metadata = JSONField(default=dict, blank=True)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at']
        indexes = [
            models.Index(fields=['user', '-taken_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.test_name} ({self.score}/{self.max_score})"


class PredictiveAnalyticsSnapshot(models.Model):
    """Store predictive signals for companies."""

    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='predictive_snapshots',
        limit_choices_to={'account_type': 'company'}
    )
    date = models.DateField(db_index=True)
    likelihood_to_hire = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    key_drivers = JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['company', 'date']
        indexes = [
            models.Index(fields=['company', '-date']),
        ]

    def __str__(self):
        return f"{self.company.email} prediction for {self.date}"


class SalaryNegotiationInsight(models.Model):
    """AI-assisted salary negotiation data for a job seeker."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='salary_insights',
        limit_choices_to={'account_type': 'personal'}
    )
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    salary_floor = models.DecimalField(max_digits=12, decimal_places=2)
    salary_ceiling = models.DecimalField(max_digits=12, decimal_places=2)
    market_rate = models.DecimalField(max_digits=12, decimal_places=2)
    confidence_score = models.FloatField(default=0.0)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.user.email} salary insight for {self.title}"


class InterviewQuestionTemplate(models.Model):
    """AI-generated interview questions per job."""

    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='question_templates',
    )
    title = models.CharField(max_length=255)
    questions = JSONField(default=list, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.job.title} questions ({self.generated_at.date()})"


class CultureFitAssessment(models.Model):
    """Culture fit assessment for a company/applicant pair."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='culture_assessments',
        limit_choices_to={'account_type': 'personal'}
    )
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='culture_assessments_received',
        limit_choices_to={'account_type': 'company'}
    )
    score = models.FloatField()
    highlights = JSONField(default=list, blank=True)
    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessed_at']

    def __str__(self):
        return f"Culture fit {self.user.email} -> {self.company.email}"


class DiversityAnalyticsSnapshot(models.Model):
    """Track diversity metrics per company per day."""

    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='diversity_snapshots',
        limit_choices_to={'account_type': 'company'}
    )
    date = models.DateField(db_index=True)
    female_ratio = models.FloatField(null=True, blank=True)
    underrepresented_ratio = models.FloatField(null=True, blank=True)
    inclusive_score = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.company.email} diversity for {self.date}"


class ReferenceCheckRequest(models.Model):
    """Track automated reference checks per application."""

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='reference_checks'
    )
    reference_name = models.CharField(max_length=200)
    email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('sent', 'Sent'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )
    feedback = JSONField(default=dict, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Reference for {self.application.id} ({self.reference_name})"
