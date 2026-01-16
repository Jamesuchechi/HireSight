"""
Admin configuration for analytics app.
"""
from django.contrib import admin
from .models import (
    ProfileView, JobView, SearchQuery,
    ApplicationMetrics, UserActivityLog,
    CompanyAnalyticsSnapshot, PersonalAnalyticsSnapshot,
    SkillAssessmentResult
)


@admin.register(ProfileView)
class ProfileViewAdmin(admin.ModelAdmin):
    list_display = ['profile_owner', 'viewer', 'viewer_ip', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['profile_owner__email', 'viewer__email', 'viewer_ip']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ['job', 'viewer', 'viewer_ip', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['job__title', 'viewer__email', 'viewer_ip']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['query_text', 'user', 'results_count', 'searched_at']
    list_filter = ['searched_at', 'results_count']
    search_fields = ['query_text', 'user__email']
    readonly_fields = ['searched_at']
    date_hierarchy = 'searched_at'


@admin.register(ApplicationMetrics)
class ApplicationMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_applications', 'applications_pending',
        'applications_screening', 'applications_interview',
        'applications_hired', 'applications_rejected'
    ]
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = [
        'date', 'total_applications', 'applications_pending',
        'applications_screening', 'applications_interview',
        'applications_offer', 'applications_hired', 'applications_rejected'
    ]


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'timestamp']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['user__email']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(CompanyAnalyticsSnapshot)
class CompanyAnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'date', 'total_jobs', 'active_jobs',
        'total_applications', 'total_hires', 'avg_time_to_hire',
        'cost_per_hire'
    ]
    list_filter = ['date']
    search_fields = ['company__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'


@admin.register(PersonalAnalyticsSnapshot)
class PersonalAnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'total_applications',
        'applications_hired', 'profile_views_count', 'avg_match_score'
    ]
    list_filter = ['date']
    search_fields = ['user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'


@admin.register(SkillAssessmentResult)
class SkillAssessmentResultAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'test_name', 'score',
        'max_score', 'passed', 'badge_awarded', 'taken_at'
    ]
    list_filter = ['passed', 'badge_awarded']
    search_fields = ['user__email', 'test_name']
    readonly_fields = ['taken_at']
    date_hierarchy = 'taken_at'
