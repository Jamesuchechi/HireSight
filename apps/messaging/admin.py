# apps/messages/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Conversation, Message, MessageAttachment,
    MessageTemplate, BlockedUser, MessageReport
)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_participants', 'subject', 'created_at', 'updated_at', 'is_archived']
    list_filter = ['created_at', 'is_archived']
    search_fields = ['subject', 'participants__email']
    filter_horizontal = ['participants', 'archived_by']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def get_participants(self, obj):
        return ", ".join([user.email for user in obj.participants.all()[:3]])
    get_participants.short_description = 'Participants'


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ['filename', 'file_type', 'file_size', 'uploaded_at']
    can_delete = True


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'sender', 'get_conversation', 'get_content_preview',
        'message_type', 'timestamp', 'is_edited', 'is_deleted'
    ]
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'timestamp']
    search_fields = ['content', 'sender__email', 'conversation__subject']
    readonly_fields = ['timestamp', 'edited_at', 'deleted_at']
    filter_horizontal = ['read_by']
    date_hierarchy = 'timestamp'
    inlines = [MessageAttachmentInline]
    
    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'sender', 'content', 'message_type')
        }),
        ('Status', {
            'fields': ('is_edited', 'edited_at', 'is_deleted', 'deleted_at', 'read_by')
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    def get_conversation(self, obj):
        return f"Conversation #{obj.conversation.id}"
    get_conversation.short_description = 'Conversation'
    
    def get_content_preview(self, obj):
        preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return preview
    get_content_preview.short_description = 'Content'


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'filename', 'file_type', 'get_file_size_mb', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['filename', 'message__sender__email']
    readonly_fields = ['uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    def get_file_size_mb(self, obj):
        size_mb = obj.file_size / (1024 * 1024)
        return f"{size_mb:.2f} MB"
    get_file_size_mb.short_description = 'File Size'


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'user', 'category', 'is_active',
        'usage_count', 'last_used', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'content', 'user__email']
    readonly_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Template Info', {
            'fields': ('user', 'name', 'subject', 'category', 'content')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'blocker', 'blocked', 'blocked_at', 'get_reason_preview']
    list_filter = ['blocked_at']
    search_fields = ['blocker__email', 'blocked__email', 'reason']
    readonly_fields = ['blocked_at']
    date_hierarchy = 'blocked_at'
    
    def get_reason_preview(self, obj):
        if obj.reason:
            return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
        return "-"
    get_reason_preview.short_description = 'Reason'


@admin.register(MessageReport)
class MessageReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'reporter', 'get_message_preview', 'reason',
        'status', 'reported_at', 'reviewed_at'
    ]
    list_filter = ['reason', 'status', 'reported_at', 'reviewed_at']
    search_fields = ['reporter__email', 'message__content', 'description']
    readonly_fields = ['reported_at']
    date_hierarchy = 'reported_at'
    
    fieldsets = (
        ('Report Info', {
            'fields': ('reporter', 'message', 'reason', 'description')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_at', 'reviewer_notes')
        }),
        ('Timestamps', {
            'fields': ('reported_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_reviewed', 'mark_as_action_taken', 'dismiss_reports']
    
    def get_message_preview(self, obj):
        preview = obj.message.content[:50] + "..." if len(obj.message.content) > 50 else obj.message.content
        return preview
    get_message_preview.short_description = 'Message'
    
    def mark_as_reviewed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='reviewed', reviewed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reports marked as reviewed")
    mark_as_reviewed.short_description = "Mark selected as reviewed"
    
    def mark_as_action_taken(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='action_taken', reviewed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reports marked as action taken")
    mark_as_action_taken.short_description = "Mark as action taken"
    
    def dismiss_reports(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='dismissed', reviewed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reports dismissed")
    dismiss_reports.short_description = "Dismiss selected reports"