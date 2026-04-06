"""
Admin interface for screening system.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
import json

from apps.applications.models import Application
from apps.assessments.models import SkillAssessmentAttempt
from apps.screening.tasks import process_resume_screening
from .models import (
    ScreeningSession, ScreeningResult, ScreeningCriteria, 
    ScreeningResultStatus, PipelineIntegration, PipelineStatus, ProgressUpdate, ProgressUpdateType,
    AIInsight, InsightFeedback, InsightType
)


class ScreeningCriteriaInline(admin.StackedInline):
    """Inline admin for screening criteria."""
    model = ScreeningCriteria
    extra = 0
    readonly_fields = ('required_skills', 'nice_to_have_skills', 'required_education', 'custom_keywords')


class ScreeningResultInline(admin.TabularInline):
    """Inline admin for screening results."""
    model = ScreeningResult
    extra = 0
    readonly_fields = ('match_score', 'status', 'processed_at')
    fields = ('match_score', 'status', 'is_shortlisted', 'processed_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ScreeningSession)
class ScreeningSessionAdmin(admin.ModelAdmin):
    """Admin interface for ScreeningSession."""
    
    list_display = (
        'id_short',
        'title',
        'company_link',
        'job_link',
        'status_badge',
        'progress_display',
        'average_score_display',
        'application_results_count',
        'created_at',
    )
    
    list_filter = ('status', 'created_at', 'company', 'job')
    
    actions = ('rescreen_with_latest_data', 'link_results_to_applications')
    
    search_fields = ('id', 'title', 'company__company_name', 'job__title')
    
    readonly_fields = (
        'id',
        'created_at',
        'completed_at',
        'total_resumes',
        'processed_resumes',
        'failed_resumes',
        'average_match_score',
        'progress_display',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'company', 'job', 'title', 'created_by')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'completed_at')
        }),
        ('Statistics', {
            'fields': (
                'total_resumes',
                'processed_resumes',
                'failed_resumes',
                'average_match_score',
                'progress_display',
            )
        }),
        ('Settings', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ScreeningCriteriaInline, ScreeningResultInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'company__user', 'job', 'created_by')
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def company_link(self, obj):
        url = reverse('admin:accounts_companyprofile_change', args=[obj.company.id])
        return format_html('<a href="{}">{}</a>', url, obj.company.company_name)
    company_link.short_description = 'Company'
    
    def job_link(self, obj):
        if obj.job:
            url = reverse('admin:jobs_job_change', args=[obj.job.id])
            return format_html('<a href="{}">{}</a>', url, obj.job.title)
        return '-'
    job_link.short_description = 'Job'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'processing': '#3b82f6',
            'completed': '#10b981',
            'failed': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def progress_display(self, obj):
        percentage_value = float(obj.progress_percentage or 0)
        display_value = f"{percentage_value:.0f}"
        color = '#10b981' if percentage_value == 100 else '#3b82f6'
        return format_html(
            '<div style="width: 100px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; background: {}; color: white; text-align: center; padding: 2px; font-size: 11px;">{}%</div>'
            '</div>',
            display_value, color, display_value
        )
    progress_display.short_description = 'Progress'
    
    def average_score_display(self, obj):
        if obj.average_match_score is None:
            return '-'
        
        score_value = float(obj.average_match_score)
        if score_value >= 90:
            color = '#059669'
        elif score_value >= 80:
            color = '#10b981'
        elif score_value >= 70:
            color = '#fbbf24'
        else:
            color = '#ef4444'
        
        rounded = f"{score_value:.0f}%"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, rounded
        )
    average_score_display.short_description = 'Avg Score'

    def application_results_count(self, obj):
        return obj.results.filter(application__isnull=False).count()
    application_results_count.short_description = 'Application-linked results'

    def rescreen_with_latest_data(self, request, queryset):
        total = 0
        for session in queryset:
            for result in session.results.filter(status=ScreeningResultStatus.COMPLETED):
                if result.resume and result.file_path:
                    process_resume_screening.delay(result.id)
                    total += 1
        self.message_user(request, f"Re-queued {total} completed results to re-screen.")
    rescreen_with_latest_data.short_description = 'Re-screen with latest data'

    def link_results_to_applications(self, request, queryset):
        linked = 0
        for session in queryset:
            for result in session.results.filter(application__isnull=True):
                application = _link_result_to_application(result)
                if application:
                    result.application = application
                    result.screening_answers = application.screening_answers or {}
                    result.assessment_data = _build_assessment_payload(application.applicant)
                    result.save(update_fields=['application', 'screening_answers', 'assessment_data'])
                    linked += 1
        self.message_user(request, f"Linked {linked} results to applications.")
    link_results_to_applications.short_description = 'Link results to applications'


class HasApplicationFilter(admin.SimpleListFilter):
    title = 'has application'
    parameter_name = 'has_application'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has Application'),
            ('no', 'Missing Application'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(application__isnull=False)
        if self.value() == 'no':
            return queryset.filter(application__isnull=True)
        return queryset


def _link_result_to_application(result):
    candidate_email = None
    if result.resume and getattr(result.resume, 'user', None):
        candidate_email = result.resume.user.email

    job_id = result.job_id or getattr(result.session, 'job_id', None)

    if result.resume:
        app = Application.objects.filter(resume=result.resume).first()
        if app:
            return app

    if job_id and candidate_email:
        app = Application.objects.filter(
            job_id=job_id,
            applicant__email__iexact=candidate_email
        ).first()
        if app:
            return app

    if candidate_email:
        return Application.objects.filter(applicant__email__iexact=candidate_email).first()

    return None


def _build_assessment_payload(user):
    attempts = SkillAssessmentAttempt.objects.filter(
        user=user,
        status='COMPLETED'
    ).select_related('test').order_by('-completed_at')

    payload = []
    for attempt in attempts:
        test = attempt.test
        skills = getattr(test, 'skills_tested', None) or []
        if skills is None:
            skills = []
        payload.append({
            'test_name': test.title if test else 'Unknown Test',
            'score': attempt.score,
            'passed': attempt.passed,
            'skills_validated': skills if isinstance(skills, list) else [skills],
            'completed_at': attempt.completed_at,
            'time_taken': getattr(attempt, 'time_taken_minutes', None) or getattr(attempt, 'time_taken', None),
        })
    return payload


@admin.register(ScreeningResult)
class ScreeningResultAdmin(admin.ModelAdmin):
    """Admin interface for ScreeningResult."""
    
    list_display = (
        'id_short',
        'session_link',
        'application_link',
        'match_score_display',
        'status_badge',
        'shortlisted_badge',
        'processed_at',
    )
    
    list_filter = ('status', 'is_shortlisted', 'processed_at', HasApplicationFilter)
    
    search_fields = ('id', 'session__title', 'resume__user__email')
    
    readonly_fields = (
        'id', 'processed_at', 'match_details_display',
        'show_screening_answers', 'show_assessment_summary'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'session', 'resume', 'job', 'application')
        }),
        ('Match Analysis', {
            'fields': ('match_score', 'match_details_display')
        }),
        ('Screening Data', {
            'fields': ('show_screening_answers', 'show_assessment_summary')
        }),
        ('Status', {
            'fields': ('status', 'processed_at', 'error_message')
        }),
        ('Recruiter Actions', {
            'fields': ('is_shortlisted', 'notes', 'rating')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('session', 'resume', 'job')
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def session_link(self, obj):
        url = reverse('admin:screening_screeningsession_change', args=[obj.session.id])
        return format_html('<a href="{}">{}</a>', url, obj.session.title)
    session_link.short_description = 'Session'

    def application_link(self, obj):
        if obj.application:
            url = reverse('admin:applications_application_change', args=[obj.application.id])
            return format_html('<a href="{}">{}</a>', url, obj.application.id)
        return '-'
    application_link.short_description = 'Application'
    
    def match_score_display(self, obj):
        score = float(obj.match_score or 0)
        if score >= 90:
            color = '#059669'
        elif score >= 80:
            color = '#10b981'
        elif score >= 70:
            color = '#fbbf24'
        else:
            color = '#ef4444'
        
        rounded = f"{score:.0f}%"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, rounded
        )
    match_score_display.short_description = 'Match'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'processing': '#3b82f6',
            'completed': '#10b981',
            'failed': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def shortlisted_badge(self, obj):
        if obj.is_shortlisted:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px;">✓</span>'
            )
        return '-'
    shortlisted_badge.short_description = 'Shortlisted'
    
    def match_details_display(self, obj):
        return format_html('<pre>{}</pre>', json.dumps(obj.match_details, indent=2))
    match_details_display.short_description = 'Match Details'

    def show_screening_answers(self, obj):
        if not obj.screening_answers:
            return '-'
        return format_html('<pre>{}</pre>', json.dumps(obj.screening_answers, indent=2))
    show_screening_answers.short_description = 'Screening Answers'

    def show_assessment_summary(self, obj):
        assessments = obj.assessment_data or []
        if not assessments:
            return '-'
        lines = []
        for entry in assessments:
            score = entry.get('score')
            skills = entry.get('skills_validated') or []
            lines.append(f"{entry.get('test_name', 'Test')}: {score}% [{', '.join(skills)}]")
        return format_html('<pre>{}</pre>', "\n".join(lines))
    show_assessment_summary.short_description = 'Assessments'


@admin.register(ScreeningCriteria)
class ScreeningCriteriaAdmin(admin.ModelAdmin):
    """Admin interface for ScreeningCriteria."""
    
    list_display = ('session', 'min_experience_years', 'weights_display')
    
    readonly_fields = ('required_skills', 'nice_to_have_skills', 'required_education', 'custom_keywords')
    
    def weights_display(self, obj):
        return f"S:{obj.weight_skills} E:{obj.weight_experience} Ed:{obj.weight_education} K:{obj.weight_keywords}"
    weights_display.short_description = 'Weights'


@admin.register(PipelineIntegration)
class PipelineIntegrationAdmin(admin.ModelAdmin):
    """Admin interface for PipelineIntegration."""
    
    list_display = (
        'result_link',
        'job_link',
        'status_badge',
        'pushed_at',
        'sync_status',
    )
    
    list_filter = ('status', 'pushed_at', 'sync_failed', 'company')
    
    search_fields = ('result__id', 'job__title', 'pipeline_id', 'result__resume__user__email')
    
    readonly_fields = (
        'id',
        'result',
        'pushed_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Relationship', {
            'fields': ('id', 'result', 'job', 'company')
        }),
        ('Pipeline Status', {
            'fields': ('status', 'pipeline_stage', 'stage_updated_at', 'pipeline_id', 'pipeline_url')
        }),
        ('Timestamps', {
            'fields': ('pushed_at', 'updated_at', 'last_synced'),
            'classes': ('collapse',)
        }),
        ('Sync Information', {
            'fields': ('sync_failed', 'sync_error'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    def result_link(self, obj):
        url = reverse('admin:screening_screeningresult_change', args=[obj.result.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            str(obj.result)[:50]
        )
    result_link.short_description = 'Result'
    
    def job_link(self, obj):
        if obj.job:
            url = reverse('admin:jobs_job_change', args=[obj.job.id])
            return format_html('<a href="{}">{}</a>', url, obj.job.title)
        return '-'
    job_link.short_description = 'Job'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'pushed': '#3b82f6',
            'hired': '#10b981',
            'rejected': '#ef4444',
            'withdrawn': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def sync_status(self, obj):
        if obj.sync_failed:
            return format_html(
                '<span style="color: red;">✗ Failed</span>'
            )
        if obj.last_synced:
            return format_html(
                '<span style="color: green;">✓ Synced</span>'
            )
        return '-'
    sync_status.short_description = 'Sync'


@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(admin.ModelAdmin):
    """Admin interface for ProgressUpdate model."""
    
    list_display = (
        'id_short',
        'session_link',
        'update_type_badge',
        'progress_bar',
        'status_badge',
        'created_at',
    )
    
    list_filter = (
        'update_type',
        'status',
        'created_at',
        ('result', admin.RelatedOnlyFieldListFilter),
    )
    
    search_fields = (
        'id',
        'session__title',
        'session__id',
        'title',
        'message',
    )
    
    readonly_fields = (
        'id',
        'session',
        'result',
        'update_type',
        'title',
        'message',
        'progress_percent',
        'current_item',
        'total_items',
        'status',
        'error_message',
        'metadata_display',
        'created_at',
    )
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'session', 'result'),
        }),
        ('Update Details', {
            'fields': ('update_type', 'title', 'message', 'status'),
        }),
        ('Progress Information', {
            'fields': ('progress_percent', 'current_item', 'total_items'),
        }),
        ('Error Handling', {
            'fields': ('error_message',),
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
    
    can_delete = True
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def session_link(self, obj):
        url = reverse('admin:screening_screeningsession_change', args=[obj.session.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.session.title[:30]
        )
    session_link.short_description = 'Session'
    
    def update_type_badge(self, obj):
        colors = {
            'upload_started': '#3b82f6',
            'screening_started': '#06b6d4',
            'screening_progress': '#8b5cf6',
            'result_analyzed': '#10b981',
            'export_started': '#f59e0b',
            'export_completed': '#10b981',
            'export_failed': '#ef4444',
            'pipeline_push_started': '#3b82f6',
            'pipeline_push_completed': '#10b981',
            'error_occurred': '#ef4444',
        }
        color = colors.get(obj.update_type, '#6b7280')
        label = obj.get_update_type_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color,
            label
        )
    update_type_badge.short_description = 'Type'
    
    def progress_bar(self, obj):
        width = obj.progress_percent
        return format_html(
            '<div style="width: 100px; height: 20px; background-color: #e5e7eb; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background-color: #3b82f6; transition: width 0.3s;"></div>'
            '</div> {}%',
            width,
            width
        )
    progress_bar.short_description = 'Progress'
    
    def status_badge(self, obj):
        colors = {
            'running': '#3b82f6',
            'completed': '#10b981',
            'failed': '#ef4444',
            'paused': '#f59e0b',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def metadata_display(self, obj):
        import json
        return format_html(
            '<pre style="background-color: #f3f4f6; padding: 10px; border-radius: 4px; max-width: 500px; overflow: auto;">{}</pre>',
            json.dumps(obj.metadata, indent=2)
        )
    metadata_display.short_description = 'Metadata'


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    """Admin interface for AI Insights."""
    
    list_display = (
        'id_short',
        'result_link',
        'insight_type_badge',
        'title',
        'confidence_display',
        'approval_badge',
        'usage_badge',
        'generation_time_display',
        'created_at',
    )
    
    list_filter = (
        'insight_type',
        'is_approved',
        'is_used',
        'created_at',
    )
    
    search_fields = (
        'id',
        'title',
        'result__candidate_name',
        'result__session__title',
    )
    
    readonly_fields = (
        'id',
        'result',
        'insight_type',
        'title',
        'content_display',
        'summary',
        'model_used',
        'tokens_used',
        'generation_time',
        'confidence_score',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'result', 'insight_type'),
        }),
        ('Content', {
            'fields': ('title', 'summary', 'content_display'),
        }),
        ('AI Metadata', {
            'fields': ('model_used', 'tokens_used', 'generation_time', 'confidence_score'),
        }),
        ('Status', {
            'fields': ('is_approved', 'is_used'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    actions = ['mark_approved', 'mark_not_approved', 'mark_used', 'mark_not_used']
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def result_link(self, obj):
        url = reverse('admin:screening_screeningresult_change', args=[obj.result.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.result.candidate_name[:30]
        )
    result_link.short_description = 'Candidate'
    
    def insight_type_badge(self, obj):
        colors = {
            'interview_questions': '#3b82f6',
            'ai_notes': '#8b5cf6',
            'rejection_reasons': '#ef4444',
            'resume_parsing': '#10b981',
        }
        color = colors.get(obj.insight_type, '#6b7280')
        label = obj.get_insight_type_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color,
            label
        )
    insight_type_badge.short_description = 'Type'
    
    def confidence_display(self, obj):
        confidence = int(obj.confidence_score * 100)
        color = '#10b981' if confidence >= 80 else '#f59e0b' if confidence >= 60 else '#ef4444'
        return format_html(
            '<div style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; text-align: center; width: 60px;">{:d}%</div>',
            color,
            confidence
        )
    confidence_display.short_description = 'Confidence'
    
    def approval_badge(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        return format_html('<span style="color: orange;">✗ Pending</span>')
    approval_badge.short_description = 'Approval'
    
    def usage_badge(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ Used</span>')
        return format_html('<span style="color: gray;">○ Unused</span>')
    usage_badge.short_description = 'Usage'
    
    def generation_time_display(self, obj):
        return format_html('<code>{:.2f}s</code>', obj.generation_time)
    generation_time_display.short_description = 'Gen Time'
    
    def content_display(self, obj):
        import json
        return format_html(
            '<pre style="background-color: #f3f4f6; padding: 10px; border-radius: 4px; max-width: 600px; overflow: auto;">{}</pre>',
            json.dumps(obj.content, indent=2)
        )
    content_display.short_description = 'Content'
    
    def mark_approved(self, request, queryset):
        updated = 0
        for obj in queryset:
            obj.mark_approved()
            updated += 1
        self.message_user(request, f'{updated} insights marked as approved.')
    mark_approved.short_description = 'Mark selected as approved'
    
    def mark_not_approved(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} insights marked as not approved.')
    mark_not_approved.short_description = 'Mark selected as not approved'
    
    def mark_used(self, request, queryset):
        updated = 0
        for obj in queryset:
            obj.mark_used()
            updated += 1
        self.message_user(request, f'{updated} insights marked as used.')
    mark_used.short_description = 'Mark selected as used'
    
    def mark_not_used(self, request, queryset):
        updated = queryset.update(is_used=False)
        self.message_user(request, f'{updated} insights marked as unused.')
    mark_not_used.short_description = 'Mark selected as unused'
    
    def has_add_permission(self, request):
        return False


class InsightFeedbackInline(admin.TabularInline):
    """Inline admin for feedback on insights."""
    model = InsightFeedback
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    can_delete = True
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(InsightFeedback)
class InsightFeedbackAdmin(admin.ModelAdmin):
    """Admin interface for Insight Feedback."""
    
    list_display = (
        'id_short',
        'insight_link',
        'rating_badge',
        'user_link',
        'has_comment',
        'created_at',
    )
    
    list_filter = (
        'rating',
        'created_at',
    )
    
    search_fields = (
        'id',
        'insight__title',
        'user__email',
        'comment',
    )
    
    readonly_fields = (
        'id',
        'insight',
        'rating',
        'comment',
        'user',
        'created_at',
    )
    
    fieldsets = (
        ('Feedback', {
            'fields': ('id', 'insight', 'rating', 'comment'),
        }),
        ('User', {
            'fields': ('user',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def insight_link(self, obj):
        url = reverse('admin:screening_aiinsight_change', args=[obj.insight.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.insight.title[:40]
        )
    insight_link.short_description = 'Insight'
    
    def rating_badge(self, obj):
        colors = {
            'helpful': '#10b981',
            'partially_helpful': '#f59e0b',
            'not_helpful': '#ef4444',
            'incorrect': '#ef4444',
        }
        color = colors.get(obj.rating, '#6b7280')
        label = obj.get_rating_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color,
            label
        )
    rating_badge.short_description = 'Rating'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def has_comment(self, obj):
        if obj.comment:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: gray;">○ No</span>')
    has_comment.short_description = 'Comment'
    
    def has_add_permission(self, request):
        return False
