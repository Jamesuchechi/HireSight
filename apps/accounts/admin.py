from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, PersonalProfile, CompanyProfile, EmailVerificationToken, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin interface for User model."""
    
    list_display = ['email', 'account_type', 'is_verified', 'is_active', 'is_staff', 'created_at']
    list_filter = ['account_type', 'is_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Account Info', {'fields': ('account_type', 'is_verified')}),
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