from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Admin interface for managing follow relationships.
    Provides comprehensive filtering, searching, and bulk actions.
    """
    
    list_display = [
        'id',
        'follower_link',
        'follower_type',
        'followed_link',
        'followed_type',
        'is_mutual',
        'created_at',
        'notification_sent'
    ]
    
    list_filter = [
        'created_at',
        'notification_sent',
        ('follower__account_type', admin.FieldListFilter),
        ('followed__account_type', admin.FieldListFilter),
    ]
    
    search_fields = [
        'follower__email',
        'followed__email',
        'follower__personalprofile__full_name',
        'followed__personalprofile__full_name',
        'followed__companyprofile__company_name',
    ]
    
    date_hierarchy = 'created_at'
    
    readonly_fields = ['created_at', 'is_mutual_display']
    
    list_per_page = 50
    
    actions = [
        'mark_notification_sent',
        'mark_notification_unsent',
        'delete_mutual_follows',
    ]
    
    fieldsets = (
        ('Relationship', {
            'fields': ('follower', 'followed')
        }),
        ('Metadata', {
            'fields': ('created_at', 'notification_sent', 'is_mutual_display'),
            'classes': ('collapse',)
        }),
    )

    def follower_link(self, obj):
        """Clickable link to follower's profile"""
        url = reverse('admin:accounts_user_change', args=[obj.follower.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.follower.get_display_name()
        )
    follower_link.short_description = 'Follower'
    follower_link.admin_order_field = 'follower__email'

    def followed_link(self, obj):
        """Clickable link to followed user's profile"""
        url = reverse('admin:accounts_user_change', args=[obj.followed.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.followed.get_display_name()
        )
    followed_link.short_description = 'Following'
    followed_link.admin_order_field = 'followed__email'

    def follower_type(self, obj):
        """Display account type with colored badge"""
        if obj.follower.account_type == 'company':
            return format_html(
                '<span style="background-color: #3B82F6; color: white; '
                'padding: 2px 8px; border-radius: 4px; font-size: 11px;">'
                'COMPANY</span>'
            )
        return format_html(
            '<span style="background-color: #10B981; color: white; '
            'padding: 2px 8px; border-radius: 4px; font-size: 11px;">'
            'PERSONAL</span>'
        )
    follower_type.short_description = 'Follower Type'

    def followed_type(self, obj):
        """Display account type with colored badge"""
        if obj.followed.account_type == 'company':
            return format_html(
                '<span style="background-color: #3B82F6; color: white; '
                'padding: 2px 8px; border-radius: 4px; font-size: 11px;">'
                'COMPANY</span>'
            )
        return format_html(
            '<span style="background-color: #10B981; color: white; '
            'padding: 2px 8px; border-radius: 4px; font-size: 11px;">'
            'PERSONAL</span>'
        )
    followed_type.short_description = 'Following Type'

    def is_mutual(self, obj):
        """Check if follow is mutual"""
        return Follow.are_mutual_followers(obj.follower, obj.followed)
    is_mutual.boolean = True
    is_mutual.short_description = 'Mutual'

    def is_mutual_display(self, obj):
        """Display mutual status in detail view"""
        if Follow.are_mutual_followers(obj.follower, obj.followed):
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Mutual Follow</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ Not Mutual</span>'
        )
    is_mutual_display.short_description = 'Mutual Status'

    # Bulk Actions
    def mark_notification_sent(self, request, queryset):
        """Mark selected follows as notification sent"""
        updated = queryset.update(notification_sent=True)
        self.message_user(
            request,
            f'{updated} follow(s) marked as notification sent.'
        )
    mark_notification_sent.short_description = 'Mark notification as sent'

    def mark_notification_unsent(self, request, queryset):
        """Mark selected follows as notification not sent"""
        updated = queryset.update(notification_sent=False)
        self.message_user(
            request,
            f'{updated} follow(s) marked as notification not sent.'
        )
    mark_notification_unsent.short_description = 'Mark notification as not sent'

    def delete_mutual_follows(self, request, queryset):
        """Delete both sides of mutual follows"""
        count = 0
        for follow in queryset:
            if Follow.are_mutual_followers(follow.follower, follow.followed):
                # Delete reverse follow as well
                Follow.objects.filter(
                    follower=follow.followed,
                    followed=follow.follower
                ).delete()
                count += 1
        
        queryset.delete()
        self.message_user(
            request,
            f'{count} mutual follow relationship(s) deleted (both directions).'
        )
    delete_mutual_follows.short_description = 'Delete mutual follows (both sides)'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'follower',
            'followed',
            'follower__personalprofile',
            'follower__companyprofile',
            'followed__personalprofile',
            'followed__companyprofile'
        )

    def has_add_permission(self, request):
        """Disable adding follows through admin (should be done through UI)"""
        return False


# Optional: Inline admin for User model
class FollowInline(admin.TabularInline):
    """
    Inline to show follows on User admin page
    """
    model = Follow
    fk_name = 'follower'
    extra = 0
    readonly_fields = ['followed', 'created_at']
    can_delete = True
    verbose_name = 'Following'
    verbose_name_plural = 'Users this user is following'
    
    fields = ['followed', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False


class FollowerInline(admin.TabularInline):
    """
    Inline to show followers on User admin page
    """
    model = Follow
    fk_name = 'followed'
    extra = 0
    readonly_fields = ['follower', 'created_at']
    can_delete = True
    verbose_name = 'Follower'
    verbose_name_plural = 'Users following this user'
    
    fields = ['follower', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False