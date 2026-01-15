from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Job, SavedJob, JobView, JobStatus


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for Job model."""

    list_display = [
        'title',
        'company_name',
        'status_badge',
        'employment_type',
        'experience_level',
        'location',
        'salary_display',
        'views_count',
        'applications_count',
        'published_at',
        'actions_column',
    ]

    list_filter = [
        'status',
        'employment_type',
        'experience_level',
        'remote_type',
        'is_remote',
        'is_featured',
        'published_at',
        'created_at',
    ]

    search_fields = [
        'title',
        'company__company_name',
        'description',
        'location',
    ]

    readonly_fields = [
        'id',
        'slug',
        'views_count',
        'applications_count',
        'created_at',
        'updated_at',
        'published_at',
        'closed_at',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'company',
                'title',
                'slug',
                'status',
                'is_featured',
            )
        }),
        ('Description', {
            'fields': (
                'description',
                'responsibilities',
                'requirements',
                'nice_to_have',
                'benefits',
            )
        }),
        ('Location & Type', {
            'fields': (
                'location',
                'is_remote',
                'remote_type',
                'timezone_preference',
            )
        }),
        ('Employment Details', {
            'fields': (
                'employment_type',
                'experience_level',
                'positions_available',
            )
        }),
        ('Salary', {
            'fields': (
                'salary_min',
                'salary_max',
                'salary_currency',
                'salary_period',
            )
        }),
        ('Application Settings', {
            'fields': (
                'application_deadline',
                'requires_cover_letter',
                'requires_portfolio',
                'screening_questions',
                'application_email',
            )
        }),
        ('Analytics', {
            'fields': (
                'views_count',
                'applications_count',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'published_at',
                'closed_at',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = [
        'make_active',
        'make_draft',
        'close_jobs',
        'feature_jobs',
        'unfeature_jobs',
    ]

    # Custom display methods
    def company_name(self, obj):
        """Display company name with link."""
        url = reverse('admin:accounts_companyprofile_change', args=[obj.company.pk])
        return format_html('<a href="{}">{}</a>', url, obj.company.company_name)
    company_name.short_description = 'Company'

    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'draft': '#6b7280',
            'active': '#10b981',
            'closed': '#ef4444',
            'archived': '#9ca3af',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'

    def salary_display(self, obj):
        """Display salary range."""
        return obj.get_salary_display()
    salary_display.short_description = 'Salary'

    def actions_column(self, obj):
        """Display action buttons."""
        buttons = []
        
        # View on site
        buttons.append(
            f'<a href="{obj.get_absolute_url()}" '
            f'style="color: #3b82f6; text-decoration: none; margin-right: 10px;" '
            f'target="_blank">👁 View</a>'
        )
        
        # Edit
        edit_url = reverse('admin:jobs_job_change', args=[obj.pk])
        buttons.append(
            f'<a href="{edit_url}" '
            f'style="color: #10b981; text-decoration: none; margin-right: 10px;">✏️ Edit</a>'
        )
        
        return format_html(' '.join(buttons))
    actions_column.short_description = 'Actions'

    # Admin actions
    @admin.action(description='Make selected jobs active')
    def make_active(self, request, queryset):
        """Set jobs to active status."""
        updated = queryset.update(status=JobStatus.ACTIVE)
        self.message_user(request, f'{updated} job(s) marked as active.')

    @admin.action(description='Make selected jobs draft')
    def make_draft(self, request, queryset):
        """Set jobs to draft status."""
        updated = queryset.update(status=JobStatus.DRAFT)
        self.message_user(request, f'{updated} job(s) marked as draft.')

    @admin.action(description='Close selected jobs')
    def close_jobs(self, request, queryset):
        """Close jobs to applications."""
        updated = queryset.update(status=JobStatus.CLOSED)
        self.message_user(request, f'{updated} job(s) closed.')

    @admin.action(description='Feature selected jobs')
    def feature_jobs(self, request, queryset):
        """Feature jobs."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} job(s) featured.')

    @admin.action(description='Unfeature selected jobs')
    def unfeature_jobs(self, request, queryset):
        """Unfeature jobs."""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} job(s) unfeatured.')

    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('company', 'company__user').annotate(
            applications_count=Count('applications')
        )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    """Admin interface for SavedJob model."""

    list_display = [
        'user_email',
        'job_title',
        'saved_at',
        'has_notes',
    ]

    list_filter = [
        'saved_at',
    ]

    search_fields = [
        'user__email',
        'job__title',
        'notes',
    ]

    readonly_fields = [
        'saved_at',
    ]

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User'

    def job_title(self, obj):
        """Display job title with link."""
        url = reverse('admin:jobs_job_change', args=[obj.job.pk])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_title.short_description = 'Job'

    def has_notes(self, obj):
        """Check if saved job has notes."""
        return bool(obj.notes)
    has_notes.boolean = True
    has_notes.short_description = 'Notes?'

    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'job', 'job__company')


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    """Admin interface for JobView model."""

    list_display = [
        'job_title',
        'user_email',
        'viewed_at',
        'ip_address',
    ]

    list_filter = [
        'viewed_at',
    ]

    search_fields = [
        'job__title',
        'user__email',
        'ip_address',
    ]

    readonly_fields = [
        'job',
        'user',
        'viewed_at',
        'ip_address',
        'user_agent',
        'referrer',
    ]

    def job_title(self, obj):
        """Display job title."""
        return obj.job.title
    job_title.short_description = 'Job'

    def user_email(self, obj):
        """Display user email or 'Anonymous'."""
        return obj.user.email if obj.user else 'Anonymous'
    user_email.short_description = 'User'

    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        return queryset.select_related('job', 'user')

    def has_add_permission(self, request):
        """Disable manual creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing."""
        return False