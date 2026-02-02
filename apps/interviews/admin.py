from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from decimal import Decimal

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.core.files.storage import default_storage
import csv

from .models import (
    Interview,
    InterviewFeedbackTemplate,
    ConsentRecord,
    AIUsageLog,
    InterviewPracticeSession,
    PracticeQuestion,
    PracticeResponse,
    PracticePerformanceReport,
)
from .tasks import generate_practice_questions, generate_practice_report
from . import admin_views


class CreatedAtRangeFilter(SimpleListFilter):
    """Custom filter rendering start/end dates for created_at."""

    title = 'created at range'
    parameter_name = 'created_at_range'
    template = 'admin/date_range_filter.html'

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.request = request

    def lookups(self, request, model_admin):
        return ()

    def queryset(self, request, queryset):
        start = request.GET.get('created_at_after')
        end = request.GET.get('created_at_before')
        if start:
            queryset = queryset.filter(created_at__date__gte=start)
        if end:
            queryset = queryset.filter(created_at__date__lte=end)
        return queryset


class PracticeResponseInline(admin.TabularInline):
    """Inline for viewing practice responses inside a session."""

    model = PracticeResponse
    fk_name = 'session'
    fields = (
        'question',
        'text_response',
        'video_url',
        'ai_score',
        'asked_at_display',
        'analysis_status',
        'submitted_at',
    )
    readonly_fields = (
        'ai_score',
        'analysis_status',
        'asked_at_display',
        'submitted_at',
    )
    extra = 0
    show_change_link = True

    def asked_at_display(self, obj):
        return obj.question.ai_generated_at if obj.question else None
    asked_at_display.short_description = 'Question generated'


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


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    """Admin interface for managing user consent records."""
    
    list_display = (
        'user',
        'consent_type_badge',
        'granted_badge',
        'granted_at_display',
        'ip_address',
        'expires_at_display'
    )
    list_filter = (
        'consent_type',
        'granted',
        'granted_at',
        'expires_at'
    )
    search_fields = (
        'user__email',
        'user__personalprofile__full_name',
        'ip_address',
        'request_id'
    )
    readonly_fields = (
        'granted_at',
        'user',
        'ip_address',
        'user_agent'
    )
    
    fieldsets = (
        ('User & Consent', {
            'fields': ('user', 'consent_type', 'granted')
        }),
        ('Timestamps', {
            'fields': ('granted_at', 'expires_at')
        }),
        ('Security', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def consent_type_badge(self, obj):
        """Display consent type with badge."""
        colors = {
            'video_recording': '#3b82f6',
            'ai_analysis': '#8b5cf6',
            'data_storage': '#ec4899',
            'performance_tracking': '#06b6d4'
        }
        color = colors.get(obj.consent_type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_consent_type_display()
        )
    consent_type_badge.short_description = 'Consent Type'
    
    def granted_badge(self, obj):
        """Display granted status with badge."""
        if obj.granted:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; border-radius: 3px;">✓ Granted</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 10px; border-radius: 3px;">✗ Declined</span>'
            )
    granted_badge.short_description = 'Status'
    
    def granted_at_display(self, obj):
        """Display granted date in user's timezone."""
        return obj.granted_at.strftime('%Y-%m-%d %H:%M')
    granted_at_display.short_description = 'Granted At'
    
    def expires_at_display(self, obj):
        """Display expiration date if present."""
        if obj.expires_at:
            return obj.expires_at.strftime('%Y-%m-%d')
        return 'No expiration'
    expires_at_display.short_description = 'Expires'


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    """Admin interface for API usage logging and cost tracking."""

    list_display = (
        'user_email_link',
        'session_link',
        'model_used_badge',
        'total_tokens',
        'cost_display',
        'created_at_display'
    )
    list_filter = (
        'model_used',
        'request_type',
        CreatedAtRangeFilter,
    )
    search_fields = (
        'user__email',
        'session__id'
    )
    readonly_fields = (
        'created_at',
        'user',
        'session',
        'request_id',
        'total_tokens',
        'estimated_cost_usd',
    )
    change_list_template = 'admin/interviews/ai_usage_log_change_list.html'
    date_hierarchy = 'created_at'
    actions = ['export_to_csv']

    fieldsets = (
        ('Request Details', {
            'fields': ('request_id', 'user', 'session', 'request_type', 'model_used', 'status')
        }),
        ('Tokens & Cost', {
            'fields': ('input_tokens', 'output_tokens', 'total_tokens', 'estimated_cost_usd'),
            'classes': ('wide',)
        }),
        ('Performance', {
            'fields': ('response_time_ms', 'created_at'),
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )

    def user_email_link(self, obj):
        if not obj.user:
            return 'System'
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email_link.short_description = 'User'
    user_email_link.admin_order_field = 'user__email'

    def session_link(self, obj):
        if not obj.session:
            return '-'
        url = reverse('admin:interviews_interviewpracticesession_change', args=[obj.session.id])
        return format_html('<a href="{}">{}</a>', url, obj.session.id)
    session_link.short_description = 'Session'
    session_link.admin_order_field = 'session__id'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data['cl']
        except (AttributeError, KeyError):
            return response

        totals = cl.queryset.aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('estimated_cost_usd')
        )
        response.context_data['aggregate_totals'] = {
            'total_tokens': totals.get('total_tokens') or 0,
            'total_cost': totals.get('total_cost') or Decimal('0.00'),
        }
        return response

    def export_to_csv(self, request, queryset):
        filename = f'ai_usage_logs_{timezone.now().strftime("%Y%m%d")}.csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow([
            'Request ID',
            'User',
            'Session',
            'Model',
            'Request Type',
            'Total Tokens',
            'Estimated Cost',
            'Status',
            'Created At'
        ])

        for log in queryset.select_related('user', 'session'):
            writer.writerow([
                log.request_id,
                log.user.email if log.user else 'System',
                str(log.session.id) if log.session else '-',
                log.get_model_used_display(),
                log.get_request_type_display(),
                log.total_tokens,
                f'{log.estimated_cost_usd:.6f}',
                log.status,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])

        return response
    export_to_csv.short_description = 'Export selected logs to CSV'

    def model_used_badge(self, obj):
        """Display model with badge."""
        colors = {
            'groq': '#4285f4',  # Keeping the blue for consistency or choosing a new one
            'mistral': '#ff6b35',
            'openai': '#10a37f'
        }
        color = colors.get(obj.model_used, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_model_used_display()
        )
    model_used_badge.short_description = 'Model'

    def cost_display(self, obj):
        """Display cost in USD."""
        return format_html(
            '<span style="color: #10b981; font-weight: bold;">${:.6f}</span>',
            float(obj.estimated_cost_usd)
        )
    cost_display.short_description = 'Cost (USD)'

    def status_badge(self, obj):
        """Display status with color."""
        colors = {
            'SUCCESS': '#10b981',
            'PARTIAL': '#f59e0b',
            'FAILED': '#ef4444',
            'FALLBACK': '#8b5cf6'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = 'Status'

    def created_at_display(self, obj):
        """Format created_at display."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = 'Created At'


@admin.register(InterviewPracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    """Admin interface for interview practice sessions."""

    list_display = (
        'candidate_email',
        'interview_type',
        'status',
        'created_at',
        'overall_score_display'
    )
    list_filter = (
        'status',
        'interview_type',
        'created_at'
    )
    search_fields = (
        'candidate__email',
        'application__job__title'
    )
    date_hierarchy = 'created_at'
    readonly_fields = (
        'created_at',
        'started_at',
        'completed_at',
        'overall_score'
    )
    inlines = [PracticeResponseInline]
    change_form_template = 'admin/interviews/practice_session_change_form.html'
    actions = (
        'regenerate_questions',
        'regenerate_report',
        'delete_with_videos',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('candidate', 'application', 'application__job')

    def overall_score_display(self, obj):
        return obj.overall_score or 0
    overall_score_display.short_description = 'Overall Score'

    def candidate_email(self, obj):
        email = obj.candidate.email if obj.candidate else 'Unknown'
        if obj.candidate:
            url = reverse('admin:accounts_user_change', args=[obj.candidate.id])
            return format_html('<a href="{}">{}</a>', url, email)
        return email
    candidate_email.short_description = 'Candidate'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        name_base = f'{self.model._meta.app_label}_{self.model._meta.model_name}'
        extra_context.update({
            'ai_logs_url': reverse(f'admin:{name_base}_ai_logs', args=[object_id]),
            'costs_url': reverse(f'admin:{name_base}_costs', args=[object_id]),
        })
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        name_base = f'{self.model._meta.app_label}_{self.model._meta.model_name}'
        custom_urls = [
            path(
                '<path:object_id>/ai-logs/',
                self.admin_site.admin_view(self.view_ai_logs),
                name=f'{name_base}_ai_logs'
            ),
            path(
                '<path:object_id>/costs/',
                self.admin_site.admin_view(self.view_costs),
                name=f'{name_base}_costs'
            ),
        ]
        return custom_urls + urls

    def view_ai_logs(self, request, object_id):
        session = get_object_or_404(self.model, pk=object_id)
        logs = session.ai_usage_logs.select_related('user').order_by('-created_at')
        totals = logs.aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('estimated_cost_usd')
        )
        context = self.admin_site.each_context(request)
        context.update({
            'opts': self.model._meta,
            'session': session,
            'logs': logs,
            'totals': {
                'total_tokens': totals.get('total_tokens') or 0,
                'total_cost': totals.get('total_cost') or Decimal('0.00'),
            },
            'title': f'AI Logs for {session}',
            'media': self.media,
        })
        return TemplateResponse(request, 'admin/interviews/practice/session_ai_logs.html', context)

    def view_costs(self, request, object_id):
        session = get_object_or_404(self.model, pk=object_id)
        logs = session.ai_usage_logs.all()
        model_breakdown = logs.values('model_used').annotate(
            tokens=Sum('total_tokens'),
            cost=Sum('estimated_cost_usd')
        ).order_by('-cost')
        totals = logs.aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('estimated_cost_usd')
        )
        context = self.admin_site.each_context(request)
        context.update({
            'opts': self.model._meta,
            'session': session,
            'model_breakdown': list(model_breakdown),
            'totals': {
                'total_tokens': totals.get('total_tokens') or 0,
                'total_cost': totals.get('total_cost') or Decimal('0.00'),
            },
            'title': f'Token Cost Breakdown for {session}',
            'media': self.media,
        })
        return TemplateResponse(request, 'admin/interviews/practice/session_costs.html', context)

    def regenerate_questions(self, request, queryset):
        sessions = queryset.filter(status=InterviewPracticeSession.Status.FAILED)
        count = 0
        for session in sessions:
            PracticeQuestion.objects.filter(session=session).delete()
            PracticePerformanceReport.objects.filter(session=session).delete()
            session.overall_score = None
            session.status = InterviewPracticeSession.Status.CREATED
            session.question_generation_state = InterviewPracticeSession.GenerationState.PENDING
            session.report_generation_state = InterviewPracticeSession.GenerationState.PENDING
            settings_data = session.settings or {}
            settings_data.pop('error_message', None)
            settings_data.pop('validation_error', None)
            session.settings = settings_data
            session.save(update_fields=[
                'overall_score',
                'status',
                'question_generation_state',
                'report_generation_state',
                'settings'
            ])
            generate_practice_questions.delay(session.id)
            count += 1
        self.message_user(request, f'Queued question regeneration for {count} session(s).')
    regenerate_questions.short_description = 'Regenerate questions for failed sessions'

    def regenerate_report(self, request, queryset):
        count = 0
        for session in queryset:
            session.report_generation_state = InterviewPracticeSession.GenerationState.IN_PROGRESS
            session.save(update_fields=['report_generation_state'])
            generate_practice_report.delay(session.id)
            count += 1
        self.message_user(request, f'Queued report regeneration for {count} session(s).')
    regenerate_report.short_description = 'Regenerate reports for selected sessions'

    def delete_with_videos(self, request, queryset):
        deleted_sessions = 0
        deleted_files = 0
        errors = []
        for session in queryset:
            responses = PracticeResponse.objects.filter(session=session)
            for response in responses:
                metrics = response.video_analysis_metrics or {}
                video_file = metrics.get('video_file')
                if video_file:
                    try:
                        if default_storage.exists(video_file):
                            default_storage.delete(video_file)
                            deleted_files += 1
                    except Exception as exc:
                        errors.append(str(exc))
            session.delete()
            deleted_sessions += 1

        msg = f'Deleted {deleted_sessions} session(s)'
        if deleted_files:
            msg += f' and {deleted_files} video asset(s)'
        if errors:
            msg += f' (errors deleting assets: {len(errors)})'
        self.message_user(request, msg)
    delete_with_videos.short_description = 'Delete sessions and associated videos'


def _get_custom_admin_urls():
    custom_urls = [
        path(
            'interviews/practice/failed-sessions/',
            admin.site.admin_view(
                admin_views.FailedSessionsView.as_view(admin_site=admin.site)
            ),
            name='admin_practice_failed_sessions'
        ),
        path(
            'interviews/practice/high-cost-users/',
            admin.site.admin_view(
                admin_views.HighCostUsersView.as_view(admin_site=admin.site)
            ),
            name='admin_practice_high_cost_users'
        ),
        path(
            'interviews/practice/analytics/',
            admin.site.admin_view(
                admin_views.PracticeAnalyticsView.as_view(admin_site=admin.site)
            ),
            name='admin_practice_analytics'
        ),
    ]
    return custom_urls + original_admin_urls()


original_admin_urls = admin.site.get_urls
admin.site.get_urls = _get_custom_admin_urls
