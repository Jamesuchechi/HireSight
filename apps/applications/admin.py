"""
Admin interface for application management.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from .models import Application, ApplicationStatusHistory, ApplicationNote, ApplicationStatus


class ApplicationStatusHistoryInline(admin.TabularInline):
    """Inline admin for application status history."""
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'changed_at', 'reason', 'notes')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ApplicationNoteInline(admin.StackedInline):
    """Inline admin for application notes."""
    model = ApplicationNote
    extra = 1
    readonly_fields = ('created_at', 'updated_at')
    fields = ('author', 'note', 'is_important', 'created_at', 'updated_at')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin interface for Application model."""
    
    list_display = (
        'id_short',
        'applicant_link',
        'job_link',
        'status_badge',
        'match_score_display',
        'rating_display',
        'shortlisted_badge',
        'applied_at',
        'days_old',
    )
    
    list_filter = (
        'status',
        'is_shortlisted',
        'rating',
        'applied_at',
        'job__company',
    )
    
    search_fields = (
        'id',
        'applicant__email',
        'applicant__personal_profile__full_name',
        'job__title',
        'job__company__company_name',
    )
    
    readonly_fields = (
        'id',
        'applied_at',
        'viewed_at',
        'last_activity_at',
        'withdrawn_at',
        'hired_at',
        'rejected_at',
        'status_changed_at',
        'match_details_display',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'job', 'applicant', 'resume', 'applied_at')
        }),
        ('Application Content', {
            'fields': ('cover_letter', 'portfolio_url', 'screening_answers', 'additional_notes')
        }),
        ('Status & Tracking', {
            'fields': (
                'status',
                'status_changed_at',
                'status_changed_by',
                'viewed_at',
                'last_activity_at',
            )
        }),
        ('AI Screening', {
            'fields': ('match_score', 'match_details_display', 'screening_notes'),
            'classes': ('collapse',)
        }),
        ('Company Internal', {
            'fields': ('recruiter_notes', 'rating', 'is_shortlisted', 'tags'),
        }),
        ('Terminal State Timestamps', {
            'fields': ('withdrawn_at', 'hired_at', 'rejected_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ApplicationStatusHistoryInline, ApplicationNoteInline]
    
    actions = [
        'mark_as_screening',
        'mark_as_interview',
        'mark_as_offer',
        'mark_as_hired',
        'mark_as_rejected',
        'add_to_shortlist',
        'remove_from_shortlist',
        'export_as_csv',
    ]
    
    date_hierarchy = 'applied_at'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'job',
            'job__company',
            'applicant',
            'applicant__personal_profile',
            'resume',
            'status_changed_by'
        ).prefetch_related(
            'status_history',
            'notes'
        )
    
    # Custom display methods
    
    def id_short(self, obj):
        """Display shortened ID."""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def applicant_link(self, obj):
        """Display applicant with link to their profile."""
        if hasattr(obj.applicant, 'personal_profile'):
            name = obj.applicant.personal_profile.full_name
        else:
            name = obj.applicant.email
        
        url = reverse('admin:accounts_user_change', args=[obj.applicant.id])
        return format_html('<a href="{}">{}</a>', url, name)
    applicant_link.short_description = 'Applicant'
    
    def job_link(self, obj):
        """Display job with link."""
        url = reverse('admin:jobs_job_change', args=[obj.job.id])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_link.short_description = 'Job'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#fbbf24',  # yellow
            'screening': '#3b82f6',  # blue
            'interview': '#8b5cf6',  # purple
            'offer': '#10b981',  # green
            'hired': '#059669',  # dark green
            'rejected': '#ef4444',  # red
            'withdrawn': '#6b7280',  # gray
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def match_score_display(self, obj):
        """Display match score with color coding."""
        if obj.match_score is None:
            return '-'
        
        if obj.match_score >= 90:
            color = '#059669'  # green
        elif obj.match_score >= 80:
            color = '#10b981'  # light green
        elif obj.match_score >= 70:
            color = '#fbbf24'  # yellow
        elif obj.match_score >= 60:
            color = '#f97316'  # orange
        else:
            color = '#ef4444'  # red
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.0f}%</span>',
            color,
            obj.match_score
        )
    match_score_display.short_description = 'Match'
    
    def rating_display(self, obj):
        """Display rating as stars."""
        if obj.rating is None:
            return '-'
        
        stars = '⭐' * obj.rating
        return format_html('<span>{}</span>', stars)
    rating_display.short_description = 'Rating'
    
    def shortlisted_badge(self, obj):
        """Display shortlisted status as badge."""
        if obj.is_shortlisted:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px;">✓ Shortlisted</span>'
            )
        return '-'
    shortlisted_badge.short_description = 'Shortlisted'
    
    def days_old(self, obj):
        """Display how many days old the application is."""
        return obj.days_since_applied
    days_old.short_description = 'Days Old'
    
    def match_details_display(self, obj):
        """Display match details in formatted way."""
        if not obj.match_details:
            return 'No match data available'
        
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.match_details, indent=2))
    match_details_display.short_description = 'Match Details'
    
    # Admin actions
    
    @admin.action(description='Mark as Screening')
    def mark_as_screening(self, request, queryset):
        """Bulk action to mark applications as screening."""
        updated = 0
        for app in queryset:
            try:
                app.update_status(ApplicationStatus.SCREENING, request.user)
                updated += 1
            except Exception:
                pass
        self.message_user(request, f'{updated} applications marked as screening.')
    
    @admin.action(description='Mark as Interview')
    def mark_as_interview(self, request, queryset):
        """Bulk action to mark applications for interview."""
        updated = 0
        for app in queryset:
            try:
                app.update_status(ApplicationStatus.INTERVIEW, request.user)
                updated += 1
            except Exception:
                pass
        self.message_user(request, f'{updated} applications marked as interview.')
    
    @admin.action(description='Mark as Offer')
    def mark_as_offer(self, request, queryset):
        """Bulk action to mark applications as offer."""
        updated = 0
        for app in queryset:
            try:
                app.update_status(ApplicationStatus.OFFER, request.user)
                updated += 1
            except Exception:
                pass
        self.message_user(request, f'{updated} applications marked as offer.')
    
    @admin.action(description='Mark as Hired')
    def mark_as_hired(self, request, queryset):
        """Bulk action to mark applications as hired."""
        updated = 0
        for app in queryset:
            try:
                app.update_status(ApplicationStatus.HIRED, request.user)
                updated += 1
            except Exception:
                pass
        self.message_user(request, f'{updated} applications marked as hired.')
    
    @admin.action(description='Mark as Rejected')
    def mark_as_rejected(self, request, queryset):
        """Bulk action to mark applications as rejected."""
        updated = 0
        for app in queryset:
            try:
                app.update_status(ApplicationStatus.REJECTED, request.user)
                updated += 1
            except Exception:
                pass
        self.message_user(request, f'{updated} applications marked as rejected.')
    
    @admin.action(description='Add to Shortlist')
    def add_to_shortlist(self, request, queryset):
        """Bulk action to add applications to shortlist."""
        updated = queryset.update(is_shortlisted=True)
        self.message_user(request, f'{updated} applications added to shortlist.')
    
    @admin.action(description='Remove from Shortlist')
    def remove_from_shortlist(self, request, queryset):
        """Bulk action to remove applications from shortlist."""
        updated = queryset.update(is_shortlisted=False)
        self.message_user(request, f'{updated} applications removed from shortlist.')
    
    @admin.action(description='Export as CSV')
    def export_as_csv(self, request, queryset):
        """Export selected applications as CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="applications_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Applicant', 'Email', 'Job', 'Company', 'Status',
            'Match Score', 'Rating', 'Shortlisted', 'Applied Date'
        ])
        
        for app in queryset:
            writer.writerow([
                str(app.id),
                app.applicant.personal_profile.full_name if hasattr(app.applicant, 'personal_profile') else app.applicant.email,
                app.applicant.email,
                app.job.title,
                app.job.company.company_name,
                app.get_status_display(),
                app.match_score or '',
                app.rating or '',
                'Yes' if app.is_shortlisted else 'No',
                app.applied_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
        
        return response


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ApplicationStatusHistory model."""
    
    list_display = ('application', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('old_status', 'new_status', 'changed_at')
    search_fields = ('application__id', 'changed_by__email', 'reason', 'notes')
    readonly_fields = ('application', 'old_status', 'new_status', 'changed_by', 'changed_at', 'reason', 'notes')
    date_hierarchy = 'changed_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    """Admin interface for ApplicationNote model."""
    
    list_display = ('application', 'author', 'note_preview', 'is_important', 'created_at')
    list_filter = ('is_important', 'created_at')
    search_fields = ('application__id', 'author__email', 'note')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def note_preview(self, obj):
        """Display note preview."""
        return obj.note[:100] + '...' if len(obj.note) > 100 else obj.note
    note_preview.short_description = 'Note'