from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from .models import (
    Resume, 
    ResumeOptimization, 
    ResumeSuggestion, 
    ResumeRewriteDraft,
    ResumeTemplate,
    ResumeTemplateCustomization,
    AIRewriteSession
)
from .parsers import resume_parser


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    """Admin interface for Resume model."""

    list_display = [
        'title',
        'user_email',
        'status_badge',
        'is_primary_badge',
        'file_size_display',
        'skills_count',
        'uploaded_at',
        'parsed_at',
        'actions_column',
    ]

    list_filter = [
        'status',
        'is_primary',
        'uploaded_at',
        'parsed_at',
    ]

    search_fields = [
        'title',
        'user__email',
        'original_filename',
        'parsed_text',
    ]

    readonly_fields = [
        'user',
        'original_filename',
        'file_size',
        'uploaded_at',
        'parsed_at',
        'parse_attempts',
        'last_parse_attempt',
        'parsed_text_display',
        'skills_display',
        'education_display',
        'contact_info_display',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'user',
                'title',
                'file',
                'original_filename',
                'file_size',
                'is_primary',
            )
        }),
        ('Parsing Status', {
            'fields': (
                'status',
                'uploaded_at',
                'parsed_at',
                'parse_attempts',
                'last_parse_attempt',
                'error_message',
            )
        }),
        ('Parsed Content', {
            'fields': (
                'parsed_text_display',
                'skills_display',
                'experience_years',
                'education_display',
                'contact_info_display',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = [
        'reparse_resumes',
        'mark_as_primary',
        'reset_parsing_status',
    ]

    # Custom display methods
    def user_email(self, obj):
        """Display user email with link."""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'

    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'uploaded': 'gray',
            'parsing': 'blue',
            'parsed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def is_primary_badge(self, obj):
        """Display primary status."""
        if obj.is_primary:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ PRIMARY</span>'
            )
        return ''
    is_primary_badge.short_description = 'Primary'

    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            if size_mb < 1:
                return f"{obj.file_size / 1024:.1f} KB"
            return f"{size_mb:.2f} MB"
        return '-'
    file_size_display.short_description = 'File Size'

    def skills_count(self, obj):
        """Display number of skills found."""
        skills = obj.get_parsed_skills_list()
        if skills:
            return len(skills)
        return 0
    skills_count.short_description = 'Skills'

    def actions_column(self, obj):
        """Display action buttons."""
        buttons = []
        
        # Download button
        buttons.append(
            f'<a href="/resumes/{obj.pk}/download/" '
            f'style="color: #3b82f6; text-decoration: none; margin-right: 10px;" '
            f'target="_blank">📥 Download</a>'
        )
        
        # Preview button
        buttons.append(
            f'<a href="/resumes/{obj.pk}/preview/" '
            f'style="color: #10b981; text-decoration: none; margin-right: 10px;" '
            f'target="_blank">👁 Preview</a>'
        )
        
        return format_html(' '.join(buttons))
    actions_column.short_description = 'Actions'

    # Readonly field displays
    def parsed_text_display(self, obj):
        """Display parsed text in a scrollable box."""
        if obj.parsed_text:
            return format_html(
                '<div style="max-height: 300px; overflow-y: auto; '
                'background-color: #f9fafb; padding: 10px; border-radius: 5px; '
                'font-family: monospace; white-space: pre-wrap;">{}</div>',
                obj.parsed_text[:2000] + ('...' if len(obj.parsed_text) > 2000 else '')
            )
        return '-'
    parsed_text_display.short_description = 'Parsed Text'

    def skills_display(self, obj):
        """Display skills as badges."""
        skills = obj.get_parsed_skills_list()
        if skills:
            badges = [
                f'<span style="background-color: #dbeafe; color: #1e40af; '
                f'padding: 2px 8px; border-radius: 3px; margin: 2px; '
                f'display: inline-block; font-size: 12px;">{skill}</span>'
                for skill in skills[:20]  # Show first 20 skills
            ]
            if len(skills) > 20:
                badges.append(f'<span>... and {len(skills) - 20} more</span>')
            return format_html(' '.join(badges))
        return '-'
    skills_display.short_description = 'Skills'

    def education_display(self, obj):
        """Display education information."""
        education = obj.get_education_list()
        if education:
            items = []
            for edu in education:
                items.append(
                    f"<li><strong>{edu.get('degree', 'N/A')}</strong> - "
                    f"{edu.get('institution', 'N/A')}<br>"
                    f"<small>{edu.get('text', '')}</small></li>"
                )
            return format_html('<ul>{}</ul>', mark_safe(''.join(items)))
        return '-'
    education_display.short_description = 'Education'

    def contact_info_display(self, obj):
        """Display contact information."""
        contact = obj.get_contact_info_dict()
        if contact:
            info = []
            if contact.get('email'):
                info.append(f"📧 {contact['email']}")
            if contact.get('phone'):
                info.append(f"📱 {contact['phone']}")
            if contact.get('linkedin'):
                info.append(f"🔗 {contact['linkedin']}")
            return format_html('<br>'.join(info))
        return '-'
    contact_info_display.short_description = 'Contact Info'

    # Admin actions
    @admin.action(description='Re-parse selected resumes')
    def reparse_resumes(self, request, queryset):
        """Re-parse selected resumes."""
        success_count = 0
        error_count = 0
        
        for resume in queryset:
            if resume.can_reparse:
                try:
                    resume.mark_as_parsing()
                    
                    result = resume_parser.parse_file(
                        resume.file.path,
                        resume.original_filename
                    )
                    
                    if result.get('success'):
                        resume.mark_as_parsed(result)
                        success_count += 1
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        resume.mark_as_failed(error_msg)
                        error_count += 1
                        
                except Exception as e:
                    resume.mark_as_failed(str(e))
                    error_count += 1
        
        self.message_user(
            request,
            f'Successfully re-parsed {success_count} resume(s). '
            f'{error_count} failed.'
        )

    @admin.action(description='Mark as primary resume')
    def mark_as_primary(self, request, queryset):
        """Mark selected resume as primary (only one allowed per user)."""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Please select exactly one resume to mark as primary.',
                level='error'
            )
            return
        
        resume = queryset.first()
        resume.is_primary = True
        resume.save()
        
        self.message_user(
            request,
            f'"{resume.title}" is now the primary resume for {resume.user.email}.'
        )

    @admin.action(description='Reset parsing status to uploaded')
    def reset_parsing_status(self, request, queryset):
        """Reset parsing status to allow re-parsing."""
        updated = queryset.update(
            status='uploaded',
            error_message='',
            parse_attempts=0,
            last_parse_attempt=None
        )
        
        self.message_user(
            request,
            f'Reset parsing status for {updated} resume(s).'
        )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


# New Template System Admin Models

@admin.register(ResumeTemplate)
class ResumeTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'tone', 'usage_count', 'is_active', 'is_premium']
    list_filter = ['category', 'tone', 'is_active', 'is_premium']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'tone', 'is_active', 'is_premium')
        }),
        ('Template Content', {
            'fields': ('html_template', 'css_styles', 'writing_style_guide')
        }),
        ('Configuration', {
            'fields': ('section_priorities', 'default_color_scheme', 'default_font_settings')
        }),
        ('Media', {
            'fields': ('preview_image', 'thumbnail_image')
        }),
        ('Statistics', {
            'fields': ('usage_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(AIRewriteSession)
class AIRewriteSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'resume', 'template', 'llm_provider', 'status', 'tokens_used', 'created_at']
    list_filter = ['llm_provider', 'status', 'created_at']
    readonly_fields = ['created_at', 'completed_at', 'tokens_used', 'processing_time_seconds']
    search_fields = ['resume__title', 'job_title', 'industry']
    fieldsets = (
        ('Session Info', {
            'fields': ('resume', 'template', 'llm_provider', 'status')
        }),
        ('Context', {
            'fields': ('job_title', 'industry', 'highlights', 'metrics_focus', 'job_description', 'additional_instructions')
        }),
        ('Content', {
            'fields': ('original_content', 'rewritten_content')
        }),
        ('Metrics', {
            'fields': ('tokens_used', 'processing_time_seconds', 'created_at', 'completed_at')
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ResumeTemplateCustomization)
class ResumeTemplateCustomizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'resume', 'template', 'created_at']
    list_filter = ['template', 'created_at']
    search_fields = ['resume__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ResumeOptimization)
class ResumeOptimizationAdmin(admin.ModelAdmin):
    list_display = ['resume', 'overall_score', 'ats_score', 'analyzed_at']
    list_filter = ['analyzed_at']
    search_fields = ['resume__title']
    readonly_fields = ['analyzed_at', 'updated_at']


@admin.register(ResumeSuggestion)
class ResumeSuggestionAdmin(admin.ModelAdmin):
    list_display = ['optimization', 'category', 'priority', 'title']
    list_filter = ['category', 'priority']
    search_fields = ['title', 'description']


@admin.register(ResumeRewriteDraft)
class ResumeRewriteDraftAdmin(admin.ModelAdmin):
    list_display = ['resume', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['resume__title']
    readonly_fields = ['created_at']