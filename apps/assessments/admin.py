import csv
import json
import logging
from io import StringIO

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone

from .ai_utils import QuestionGenerator
from .models import (
    QuestionPool, SkillTest, SkillAssessmentAttempt, 
    SkillBadge, AssessmentCategory, StudyGroup,
    StudyGroupMembership, GroupChallenge,
    QuestionDiscussion, BookmarkedQuestion, Achievement,
    UserAchievement
)

logger = logging.getLogger(__name__)


@admin.register(QuestionPool)
class QuestionPoolAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'skill_name', 'difficulty', 'question_type', 'points', 'success_rate_display', 'times_used', 'is_active', 'is_verified', 'flag_count']
    list_filter = ['skill_name', 'difficulty', 'question_type', 'is_active', 'is_verified', 'is_flagged', 'created_at']
    search_fields = ['skill_name', 'question', 'explanation']
    ordering = ['-created_at']
    readonly_fields = ['id', 'times_used', 'times_correct', 'average_time_taken', 'created_at', 'updated_at', 'success_rate_display']
    
    fieldsets = (
        ('Question Details', {
            'fields': ('skill_name', 'difficulty', 'question_type', 'question', 'options', 'correct_answer', 'explanation')
        }),
        ('Scoring & Timing', {
            'fields': ('points', 'estimated_time_seconds')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'is_flagged')
        }),
        ('Moderation', {
            'fields': ('flag_count', 'explanation_upvotes'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('times_used', 'times_correct', 'average_time_taken', 'success_rate_display'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_preview.short_description = 'Question'
    
    def success_rate_display(self, obj):
        rate = obj.get_success_rate()
        color = 'green' if rate >= 70 else 'orange' if rate >= 50 else 'red'
        formatted = f"{rate:.1f}%"
        return format_html('<span style="color: {};">{}</span>', color, formatted)
    success_rate_display.short_description = 'Success Rate'
    
    actions = ['mark_verified', 'mark_unverified', 'activate', 'deactivate', 'verify_unverified']
    
    def mark_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} question(s) marked as verified.')
    mark_verified.short_description = 'Mark selected as verified'
    
    def mark_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} question(s) marked as unverified.')
    mark_unverified.short_description = 'Mark selected as unverified'
    
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} question(s) activated.')
    activate.short_description = 'Activate selected questions'
    
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} question(s) deactivated.')
    deactivate.short_description = 'Deactivate selected questions'

    def verify_unverified(self, request, queryset):
        updated = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(request, f'{updated} question(s) verified.')
    verify_unverified.short_description = 'Verify selected unverified questions'


@admin.register(SkillTest)
class SkillTestAdmin(admin.ModelAdmin):
    list_display = ['title', 'skill_name', 'test_type', 'difficulty', 'question_count_display', 'duration_minutes', 'passing_score', 'pass_rate_display', 'total_attempts', 'is_active', 'is_featured']
    list_filter = ['test_type', 'difficulty', 'is_active', 'is_featured', 'created_at']
    search_fields = ['title', 'skill_name', 'description']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-created_at']
    readonly_fields = ['id', 'total_attempts', 'total_passed', 'average_score', 'average_completion_time', 'created_at', 'updated_at', 'pass_rate_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'skill_name', 'description', 'test_type', 'difficulty')
        }),
        ('Test Configuration', {
            'fields': ('duration_minutes', 'passing_score', 'required_skills')
        }),
        ('Static Test Questions', {
            'fields': ('questions',),
            'classes': ('collapse',),
            'description': 'For static tests only'
        }),
        ('Dynamic Test Configuration', {
            'fields': ('question_count', 'question_pool_filters'),
            'classes': ('collapse',),
            'description': 'For dynamic tests only'
        }),
        ('Settings', {
            'fields': ('version', 'is_active', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('total_attempts', 'total_passed', 'average_score', 'average_completion_time', 'pass_rate_display'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_count_display(self, obj):
        return obj.get_question_count()
    question_count_display.short_description = 'Questions'
    
    def pass_rate_display(self, obj):
        rate = obj.get_pass_rate()
        color = 'green' if rate >= 70 else 'orange' if rate >= 50 else 'red'
        formatted = f"{rate:.1f}%"
        return format_html('<span style="color: {};">{}</span>', color, formatted)
    pass_rate_display.short_description = 'Pass Rate'
    
    actions = [
        'activate', 'deactivate', 'feature', 'unfeature',
        'duplicate_test', 'generate_questions_with_ai',
        'export_questions_to_csv', 'send_test_invitations'
    ]
    
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} test(s) activated.')
    activate.short_description = 'Activate selected tests'
    
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} test(s) deactivated.')
    deactivate.short_description = 'Deactivate selected tests'
    
    def feature(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} test(s) featured.')
    feature.short_description = 'Feature selected tests'
    
    def unfeature(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} test(s) unfeatured.')
    unfeature.short_description = 'Unfeature selected tests'
    
    def duplicate_test(self, request, queryset):
        for test in queryset:
            test.pk = None
            test.title = f"{test.title} (Copy)"
            test.slug = None
            test.is_active = False
            test.save()
        self.message_user(request, f'{queryset.count()} test(s) duplicated.')
    duplicate_test.short_description = 'Duplicate selected tests'

    def generate_questions_with_ai(self, request, queryset):
        generator = QuestionGenerator()
        total_created = 0
        for test in queryset:
            try:
                created = generator.bulk_generate_for_test(test)
                total_created += created
            except Exception as exc:
                logger.error(f"AI generation failed for {test.title}: {exc}")
        self.message_user(request, f'Generated {total_created} AI questions for {queryset.count()} test(s).')
    generate_questions_with_ai.short_description = 'Generate questions with AI for selected tests'

    def export_questions_to_csv(self, request, queryset):
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'Test Title', 'Skill', 'Difficulty', 'Question', 'Options',
            'Correct Answer', 'Explanation', 'Points', 'Time Estimate',
            'Verified', 'Created At'
        ])

        skill_names = [test.skill_name for test in queryset]
        questions = QuestionPool.objects.filter(
            skill_name__in=skill_names
        ).order_by('skill_name', 'difficulty', 'created_at')

        for question in questions:
            writer.writerow([
                next((test.title for test in queryset if test.skill_name.lower() == question.skill_name.lower()), question.skill_name),
                question.skill_name,
                question.difficulty,
                question.question,
                json.dumps(question.options),
                json.dumps(question.correct_answer),
                question.explanation,
                question.points,
                question.estimated_time_seconds,
                question.is_verified,
                question.created_at.isoformat()
            ])

        response = HttpResponse(buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="assessment_questions.csv"'
        return response
    export_questions_to_csv.short_description = 'Export related question bank to CSV'

    def send_test_invitations(self, request, queryset):
        user_model = get_user_model()
        personal_users = user_model.objects.filter(account_type='personal').select_related('personal_profile')
        sender = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hiresight.io')
        total_sent = 0

        for test in queryset:
            link = request.build_absolute_uri(reverse('assessments:test_detail', kwargs={'slug': test.slug}))
            invited = 0
            for user in personal_users:
                if invited >= 5:
                    break
                profile = getattr(user, 'personal_profile', None)
                if not profile:
                    continue
                skills = {
                    entry.get('skill', '').lower()
                    for entry in getattr(profile, 'skills', [])
                    if entry.get('skill')
                }
                if test.skill_name.lower() not in skills:
                    continue
                if not user.email:
                    continue
                subject = f"New {test.skill_name} assessment on HireSight"
                message = (
                    f"Hi {user.get_full_name() or user.email},\n\n"
                    f"Based on your skills, we recommend the '{test.title}' assessment.\n"
                    f"Resume or start it here: {link}\n\n"
                    "Keep tracking your verified skills with HireSight."
                )
                send_mail(subject, message, sender, [user.email], fail_silently=True)
                invited += 1
                total_sent += 1
            if invited:
                logger.info(f"Sent {invited} invitations for {test.title}")

        self.message_user(request, f'Sent {total_sent} test invitations.')
    send_test_invitations.short_description = 'Send test invitations to matching users'


@admin.register(SkillAssessmentAttempt)
class SkillAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'test_name', 'status', 'score_display', 'passed_display', 'time_taken_minutes', 'started_at', 'completed_at']
    list_filter = ['status', 'passed', 'test__skill_name', 'started_at', 'completed_at']
    search_fields = ['user__email', 'test__title', 'ip_address']
    ordering = ['-started_at']
    readonly_fields = ['id', 'user', 'test', 'started_at', 'completed_at', 'score', 'passed', 'points_earned', 'points_possible', 'time_taken_minutes', 'question_results']
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('id', 'user', 'test', 'status', 'started_at', 'completed_at')
        }),
        ('Questions & Answers', {
            'fields': ('frozen_questions', 'answers'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('score', 'passed', 'points_earned', 'points_possible', 'time_taken_minutes', 'time_limit_exceeded'),
            'classes': ('collapse',)
        }),
        ('Detailed Results', {
            'fields': ('question_results',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def test_name(self, obj):
        return obj.test.title
    test_name.short_description = 'Test'
    test_name.admin_order_field = 'test__title'
    
    def score_display(self, obj):
        if obj.score is None:
            return '-'
        color = 'green' if obj.score >= 70 else 'orange' if obj.score >= 50 else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, f'{obj.score}%')
    score_display.short_description = 'Score'
    score_display.admin_order_field = 'score'
    
    def passed_display(self, obj):
        if obj.passed is None:
            return '-'
        return format_html(
            '<span style="color: {};">●</span> {}',
            'green' if obj.passed else 'red',
            'Passed' if obj.passed else 'Failed'
        )
    passed_display.short_description = 'Result'
    passed_display.admin_order_field = 'passed'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SkillBadge)
class SkillBadgeAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'badge_name', 'badge_level', 'test_score', 'issued_at', 'is_public', 'view_count', 'verification_link']
    list_filter = ['badge_level', 'is_public', 'issued_at']
    search_fields = ['user__email', 'badge_name', 'verification_code']
    ordering = ['-issued_at']
    readonly_fields = ['id', 'user', 'test', 'attempt', 'badge_name', 'badge_level', 'issued_at', 'verification_code', 'verification_url', 'view_count', 'verification_link']
    
    fieldsets = (
        ('Badge Information', {
            'fields': ('id', 'user', 'test', 'attempt', 'badge_name', 'badge_level', 'badge_image_url')
        }),
        ('Verification', {
            'fields': ('verification_code', 'verification_url', 'verification_link', 'is_verified')
        }),
        ('Settings', {
            'fields': ('is_public', 'expires_at')
        }),
        ('Statistics', {
            'fields': ('view_count', 'shared_with_companies'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('issued_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def test_score(self, obj):
        return f"{obj.attempt.score}%"
    test_score.short_description = 'Score'
    
    def verification_link(self, obj):
        if obj.verification_code:
            url = reverse('assessments:verify_badge', args=[obj.verification_code])
            return format_html('<a href="{}" target="_blank">View Badge</a>', url)
        return '-'
    verification_link.short_description = 'Badge Link'
    
    def has_add_permission(self, request):
        return False


@admin.register(AssessmentCategory)
class AssessmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_display', 'test_count', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    filter_horizontal = ['tests']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Tests', {
            'fields': ('tests',)
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    def icon_display(self, obj):
        if obj.icon:
            return format_html('<span style="font-size: 24px;">{}</span>', obj.icon)
        return '-'
    icon_display.short_description = 'Icon'
    
    def test_count(self, obj):
        return obj.tests.count()
    test_count.short_description = 'Tests'


class StudyGroupMembershipInline(admin.TabularInline):
    model = StudyGroupMembership
    extra = 0
    verbose_name = "Membership"
    verbose_name_plural = "Memberships"


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'skill_focus', 'creator_email', 'member_count',
        'is_public', 'max_members', 'created_at'
    ]
    list_filter = ['is_public', 'skill_focus']
    search_fields = ['name', 'description', 'skill_focus', 'creator__email']
    inlines = [StudyGroupMembershipInline]
    readonly_fields = ['member_count', 'created_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'skill_focus')
        }),
        ('Settings', {
            'fields': ('creator', 'is_public', 'max_members')
        }),
        ('Stats', {
            'fields': ('member_count', 'created_at')
        }),
    )

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'

    def creator_email(self, obj):
        return obj.creator.email
    creator_email.short_description = 'Creator'


@admin.register(StudyGroupMembership)
class StudyGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'group', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__email', 'group__name']
    readonly_fields = ['joined_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'


@admin.register(GroupChallenge)
class GroupChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'test', 'status_label', 'start_date', 'end_date', 'leaderboard_link']
    list_filter = ['group', 'test', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'group__name', 'test__title']
    readonly_fields = ['created_at']

    fieldsets = (
        (None, {
            'fields': ('group', 'test', 'title', 'description', 'prize_description')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def status_label(self, obj):
        now = timezone.now()
        if obj.start_date <= now <= obj.end_date:
            return format_html('<span style="color: green;">Active</span>')
        if now < obj.start_date:
            return format_html('<span style="color: blue;">Upcoming</span>')
        return format_html('<span style="color: red;">Closed</span>')
    status_label.short_description = 'Status'

    def leaderboard_link(self, obj):
        url = reverse('assessments:group_leaderboard', kwargs={'group_id': obj.group.id})
        return format_html('<a href="{}" target="_blank">Leaderboard</a>', url)
    leaderboard_link.short_description = 'Leaderboard'


@admin.register(QuestionDiscussion)
class QuestionDiscussionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'user', 'upvote_count', 'created_at']
    list_filter = ['question__skill_name', 'user']
    search_fields = ['question__question', 'user__email', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def question_preview(self, obj):
        return f"{obj.question.skill_name}: {obj.question.question[:60]}..."
    question_preview.short_description = 'Question'

    def upvote_count(self, obj):
        return obj.upvotes.count()
    upvote_count.short_description = 'Upvotes'


@admin.register(BookmarkedQuestion)
class BookmarkedQuestionAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'question_preview', 'notes_summary', 'created_at']
    list_filter = ['question__skill_name', 'created_at']
    search_fields = ['user__email', 'question__question', 'notes']
    readonly_fields = ['created_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def question_preview(self, obj):
        return f"{obj.question.skill_name}: {obj.question.question[:60]}..."
    question_preview.short_description = 'Question'

    def notes_summary(self, obj):
        if obj.notes:
            return obj.notes[:60] + ('…' if len(obj.notes) > 60 else '')
        return '-'
    notes_summary.short_description = 'Notes'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'type', 'icon']
    search_fields = ['name', 'code', 'description']
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description', 'icon', 'type')
        }),
        ('Criteria', {
            'fields': ('criteria',)
        }),
    )
    readonly_fields = ['code']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'achievement_name', 'earned_at']
    list_filter = ['achievement', 'earned_at']
    search_fields = ['user__email', 'achievement__name']
    readonly_fields = ['earned_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def achievement_name(self, obj):
        return obj.achievement.name
    achievement_name.short_description = 'Achievement'
