from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User,
    PersonalProfile,
    CompanyProfile,
    UserProfile,
    EmailVerificationToken,
    PasswordResetToken,
    APIKey,
    ProfileView,
    UserSession,
    AccountDeletionLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin interface for User model."""
    
    list_display = ['email', 'account_type', 'email_verified', 'is_active', 'is_staff', 'created_at']
    list_filter = ['account_type', 'email_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Account Info', {'fields': ('account_type', 'email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'account_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(PersonalProfile)
class PersonalProfileAdmin(admin.ModelAdmin):
    """Admin interface for Personal Profile."""
    
    list_display = ['full_name', 'user_email', 'location', 'availability', 'profile_visibility', 'completion_badge', 'created_at']
    list_filter = ['availability', 'profile_visibility', 'created_at']
    search_fields = ['full_name', 'user__email', 'headline']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Basic Info', {'fields': ('full_name', 'headline', 'avatar', 'location', 'phone', 'bio')}),
        ('Professional Data', {'fields': ('skills', 'experience', 'education', 'certifications', 'portfolio_links')}),
        ('Job Preferences', {'fields': ('preferred_job_types', 'salary_expectation_min', 'salary_expectation_max', 'salary_currency', 'availability')}),
        ('Settings', {'fields': ('profile_visibility', 'resume_primary_id')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def completion_badge(self, obj):
        score = obj.calculate_completion_score()
        if score >= 80:
            color = 'green'
        elif score >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            score
        )
    completion_badge.short_description = 'Profile Completion'


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    """Admin interface for Company Profile."""
    
    list_display = ['company_name', 'user_email', 'industry', 'company_size', 'verification_badge', 'created_at']
    list_filter = ['verification_status', 'company_size', 'industry', 'created_at']
    search_fields = ['company_name', 'user__email', 'industry']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Basic Info', {'fields': ('company_name', 'logo', 'industry', 'company_size')}),
        ('Company Details', {'fields': ('locations', 'website', 'description', 'mission', 'culture', 'founded_year')}),
        ('Benefits & Team', {'fields': ('benefits', 'team_photos')}),
        ('Verification', {'fields': ('verification_status', 'verification_docs')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def verification_badge(self, obj):
        status_colors = {
            'verified': 'green',
            'pending': 'orange',
            'unverified': 'red'
        }
        color = status_colors.get(obj.verification_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_verification_status_display()
        )
    verification_badge.short_description = 'Verification'


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin interface for Email Verification Tokens."""
    
    list_display = ['user_email', 'token_preview', 'expires_at', 'is_expired_badge', 'created_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def token_preview(self, obj):
        return f"{obj.token[:20]}..."
    token_preview.short_description = 'Token'
    
    def is_expired_badge(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_badge.short_description = 'Status'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin interface for Password Reset Tokens."""
    
    list_display = ['user_email', 'token_preview', 'expires_at', 'is_expired_badge', 'created_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def token_preview(self, obj):
        return f"{obj.token[:20]}..."
    token_preview.short_description = 'Token'
    
    def is_expired_badge(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_badge.short_description = 'Status'
    


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin interface for API keys."""
    list_display = ['name', 'user', 'key_prefix_display', 'is_active', 'created_at', 'last_used_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__email', 'key']
    readonly_fields = ['id', 'key', 'key_prefix', 'created_at', 'last_used_at']
    date_hierarchy = 'created_at'
    
    def key_prefix_display(self, obj):
        """Display key prefix."""
        return f"{obj.key_prefix}..."
    key_prefix_display.short_description = 'Key Prefix'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user')


@admin.register(ProfileView)
class ProfileViewAdmin(admin.ModelAdmin):
    """Admin interface for profile views."""
    list_display = ['profile_user', 'viewer_display', 'viewed_at', 'device_info']
    list_filter = ['viewed_at']
    search_fields = ['profile_user__email', 'viewer__email', 'viewer_ip']
    readonly_fields = ['id', 'profile_user', 'viewer', 'viewer_ip', 'viewer_user_agent', 'viewed_at']
    date_hierarchy = 'viewed_at'
    
    def viewer_display(self, obj):
        """Display viewer name or IP."""
        if obj.viewer:
            return obj.viewer.get_full_name()
        return f"Anonymous ({obj.viewer_ip})"
    viewer_display.short_description = 'Viewer'
    
    def device_info(self, obj):
        """Display device information."""
        if obj.viewer_user_agent:
            # Parse user agent to show browser/device
            import user_agents
            ua = user_agents.parse(obj.viewer_user_agent)
            return f"{ua.browser.family} on {ua.os.family}"
        return "Unknown"
    device_info.short_description = 'Device'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('profile_user', 'viewer')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for user sessions."""
    list_display = ['user', 'device_type', 'location_display', 'ip_address', 'last_activity', 'is_active']
    list_filter = ['device_type', 'created_at', 'last_activity']
    search_fields = ['user__email', 'ip_address', 'location']
    readonly_fields = ['id', 'user', 'session_key', 'ip_address', 'user_agent', 'created_at', 'last_activity']
    date_hierarchy = 'last_activity'
    
    def location_display(self, obj):
        """Display location."""
        return obj.location if obj.location else "Unknown"
    location_display.short_description = 'Location'
    
    def is_active(self, obj):
        """Display if session is active."""
        is_active = not obj.is_expired()
        color = 'green' if is_active else 'red'
        status = 'Active' if is_active else 'Expired'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            status
        )
    is_active.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user')


@admin.register(AccountDeletionLog)
class AccountDeletionLogAdmin(admin.ModelAdmin):
    """Admin interface for account deletion logs."""
    list_display = ['user_email', 'account_type', 'deleted_at', 'account_age_days', 'deleted_by_user']
    list_filter = ['account_type', 'deleted_by_user', 'deleted_at']
    search_fields = ['user_email', 'deletion_reason']
    readonly_fields = ['id', 'user_email', 'account_type', 'deletion_reason', 'deleted_at', 
                      'deleted_by_user', 'account_age_days', 'total_applications', 'total_job_posts']
    date_hierarchy = 'deleted_at'
    
    def has_add_permission(self, request):
        """Disable adding deletion logs manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing deletion logs."""
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin view for user profiles with practice toggles."""

    list_display = ['user_email', 'full_name', 'practice_enabled_badge', 'created_at']
    list_filter = ['practice_enabled', 'created_at']
    search_fields = ['user__email', 'full_name']
    readonly_fields = ['created_at', 'updated_at']
    actions = [
        'enable_practice',
        'disable_practice',
        'enable_practice_for_premium_users'
    ]

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Contact Info', {'fields': ('full_name', 'professional_title', 'phone', 'location')}),
        ('Practice Controls', {'fields': ('practice_enabled',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def practice_enabled_badge(self, obj):
        if obj.practice_enabled:
            color = '#10b981'
            text = 'Enabled'
        else:
            color = '#ef4444'
            text = 'Disabled'
        return format_html(
            '<span style="color: {}; font-weight:bold;">{}</span>',
            color,
            text
        )
    practice_enabled_badge.short_description = 'Practice Access'

    def enable_practice(self, request, queryset):
        updated = queryset.update(practice_enabled=True)
        self.message_user(request, f'Practice enabled for {updated} profile(s).')
    enable_practice.short_description = 'Enable practice for selected profiles'

    def disable_practice(self, request, queryset):
        updated = queryset.update(practice_enabled=False)
        self.message_user(request, f'Practice disabled for {updated} profile(s).')
    disable_practice.short_description = 'Disable practice for selected profiles'

    def enable_practice_for_premium_users(self, request, queryset):
        premium_ids = [
            profile.id for profile in queryset
            if getattr(profile, 'is_premium', False)
        ]
        if not premium_ids:
            self.message_user(request, 'No premium user profiles found in selection.', level=messages.INFO)
            return
        updated = queryset.filter(id__in=premium_ids).update(practice_enabled=True)
        self.message_user(request, f'Enabled practice for {updated} premium profile(s).')
    enable_practice_for_premium_users.short_description = 'Enable practice for premium users'
