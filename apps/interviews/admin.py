from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Interview, InterviewFeedbackTemplate


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for Interview management
    """
    
    list_display = (
        'id_short',
        'candidate_email',
        'job_title',
        'company_name',
        'interview_type_badge',
        'status_badge',
        'candidate_response_badge',
        'scheduled_date_display',
        'duration_display',
        'reschedule_count',
        'actions_column'
    )
    
    list_filter = (
        'status',
        'interview_type',
        'scheduled_date',
        'created_at',
        'reschedule_count',
    )
    
    search_fields = (
        'application__applicant__email',
        'application__applicant__personalprofile__full_name',
        'interviewer_name',
        'interviewer_email',
        'application__job__title',
        'application__job__company__company_name',
    )
    
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'created_by',
        'cancelled_by',
        'cancelled_at',
        'original_scheduled_date',
        'reschedule_count',
        'reminder_24h_sent',
        'reminder_1h_sent',
        'proposed_times',
        'candidate_response',
    )
    
    fieldsets = (
        ('Interview Information', {
            'fields': (
                'id',
                'application',
                'interview_type',
                'status',
            )
        }),
        ('Scheduling Details', {
            'fields': (
                'scheduled_date',
                'duration_minutes',
                'timezone_name',
                'original_scheduled_date',
                'reschedule_count',
            )
        }),
        ('Location & Access', {
            'fields': (
                'location',
                'video_link',
                'dial_in_number',
            )
        }),
        ('Interviewer Details', {
            'fields': (
                'interviewer_name',
                'interviewer_email',
                'additional_interviewers',
            )
        }),
        ('Candidate Response', {
            'fields': (
                'candidate_response',
                'proposed_times',
            ),
            'classes': ('collapse',)
        }),
        ('Notes & Feedback', {
            'fields': (
                'candidate_instructions',
                'company_notes',
                'completion_notes',
                'interview_rating',
                'interviewer_feedback',
            )
        }),
        ('Reminders', {
            'fields': (
                'reminder_24h_sent',
                'reminder_1h_sent',
            ),
            'classes': ('collapse',)
        }),
        ('Cancellation Details', {
            'fields': (
                'cancelled_by',
                'cancelled_at',
                'cancellation_reason',
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'scheduled_date'
    
    ordering = ('-scheduled_date',)
    
    actions = [
        'mark_as_completed',
        'mark_as_cancelled',
        'send_reminder_now',
        'export_to_calendar',
    ]
    
    def id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def candidate_email(self, obj):
        """Display candidate email with link"""
        email = obj.application.applicant.email
        url = reverse('admin:auth_user_change', args=[obj.application.applicant.id])
        return format_html('<a href="{}">{}</a>', url, email)
    candidate_email.short_description = 'Candidate'
    
    def job_title(self, obj):
        """Display job title with link"""
        title = obj.application.job.title
        return format_html('<strong>{}</strong>', title)
    job_title.short_description = 'Job'
    
    def company_name(self, obj):
        """Display company name"""
        return obj.application.job.company.company_name
    company_name.short_description = 'Company'
    
    def interview_type_badge(self, obj):
        """Display interview type as badge"""
        colors = {
            'PHONE': '#3B82F6',      # Blue
            'VIDEO': '#10B981',      # Green
            'ONSITE': '#F59E0B',     # Orange
            'TECHNICAL': '#8B5CF6',  # Purple
            'BEHAVIORAL': '#EC4899', # Pink
            'PANEL': '#6366F1',      # Indigo
            'CULTURE_FIT': '#14B8A6',# Teal
            'FINAL': '#EF4444',      # Red
        }
        color = colors.get(obj.interview_type, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_interview_type_display()
        )
    interview_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'SCHEDULED': '#10B981',   # Green
            'RESCHEDULED': '#F59E0B', # Orange
            'COMPLETED': '#3B82F6',   # Blue
            'CANCELLED': '#EF4444',   # Red
            'NO_SHOW': '#6B7280',     # Gray
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
        status_badge.short_description = 'Status'
    
    def candidate_response_badge(self, obj):
        """Display candidate response state"""
        colors = {
            'PENDING': '#FBBF24',
            'ACCEPTED': '#10B981',
            'DECLINED': '#EF4444',
            'PROPOSED_RESCHEDULE': '#3B82F6',
        }
        color = colors.get(obj.candidate_response, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            dict(Interview._meta.get_field('candidate_response').choices).get(obj.candidate_response, obj.candidate_response)
        )
    candidate_response_badge.short_description = 'Response'
    
    def scheduled_date_display(self, obj):
        """Display scheduled date with time until in interview timezone"""
        scheduled = self._get_scheduled_time_in_timezone(obj)
        now = timezone.now().astimezone(scheduled.tzinfo)
        if scheduled > now:
            delta = scheduled - now
            days = delta.days
            hours = delta.seconds // 3600
            
            if days > 0:
                time_until = f"in {days}d {hours}h"
            else:
                time_until = f"in {hours}h"
            
            time_html = format_html(
                '{}<br><small style="color: #10B981;">{}</small>',
                scheduled.strftime('%Y-%m-%d %H:%M %Z'),
                time_until
            )
        else:
            time_html = format_html(
                '{}<br><small style="color: #EF4444;">Past</small>',
                scheduled.strftime('%Y-%m-%d %H:%M %Z')
            )

        return time_html
    scheduled_date_display.short_description = 'Scheduled'
    
    def actions_column(self, obj):
        """Display action buttons"""
        buttons = []
        
        if obj.can_reschedule():
            buttons.append(
                '<a href="{}" style="color: #3B82F6;">Reschedule</a>'.format(
                    reverse('admin:interviews_interview_change', args=[obj.id])
                )
            )
        
        if obj.can_cancel():
            buttons.append(
                '<a href="{}" style="color: #EF4444;">Cancel</a>'.format(
                    reverse('admin:interviews_interview_delete', args=[obj.id])
                )
            )
        
        if obj.can_mark_completed():
            buttons.append(
                '<a href="{}" style="color: #10B981;">Complete</a>'.format(
                    reverse('admin:interviews_interview_change', args=[obj.id])
                )
            )
        
        return format_html(' | '.join(buttons)) if buttons else '-'
    actions_column.short_description = 'Actions'
    
    # Admin actions
    
    def mark_as_completed(self, request, queryset):
        """Mark selected interviews as completed"""
        updated = queryset.filter(
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED],
            scheduled_date__lte=timezone.now()
        ).update(status=Interview.InterviewStatus.COMPLETED)
        
        self.message_user(request, f'{updated} interview(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected interviews as cancelled"""
        updated = queryset.exclude(
            status__in=[Interview.InterviewStatus.CANCELLED, Interview.InterviewStatus.COMPLETED]
        ).update(
            status=Interview.InterviewStatus.CANCELLED,
            cancelled_at=timezone.now()
        )
        
        self.message_user(request, f'{updated} interview(s) cancelled.')
    mark_as_cancelled.short_description = 'Cancel selected interviews'
    
    def send_reminder_now(self, request, queryset):
        """Send reminder emails immediately"""
        from .tasks import send_interview_invitation
        
        count = 0
        for interview in queryset.filter(
            status__in=[Interview.InterviewStatus.SCHEDULED, Interview.InterviewStatus.RESCHEDULED],
            scheduled_date__gte=timezone.now()
        ):
            send_interview_invitation.delay(interview.id, is_reschedule=False)
            count += 1
        
        self.message_user(request, f'Reminder sent for {count} interview(s).')
    send_reminder_now.short_description = 'Send reminder now'
    
    def export_to_calendar(self, request, queryset):
        """Export selected interviews to calendar"""
        # This would generate a combined .ics file
        self.message_user(request, 'Calendar export functionality coming soon.')
    export_to_calendar.short_description = 'Export to calendar'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'application__applicant',
            'application__job__company',
            'created_by',
            'cancelled_by'
        )

    def _get_scheduled_time_in_timezone(self, obj):
        """Convert scheduled_date to the interview's timezone"""
        tz_name = obj.timezone_name or 'UTC'
        try:
            target_tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            target_tz = ZoneInfo('UTC')

        return timezone.localtime(obj.scheduled_date, target_tz)


@admin.register(InterviewFeedbackTemplate)
class InterviewFeedbackTemplateAdmin(admin.ModelAdmin):
    """Admin UI for feedback templates."""

    list_display = ('name', 'company', 'interview_type', 'created_at')
    list_filter = ('interview_type', 'company')
    search_fields = ('name', 'company__email')
    readonly_fields = ('created_at',)
