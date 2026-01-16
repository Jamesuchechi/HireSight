from django.db import models

from apps.accounts.models import User


class NotificationType(models.TextChoices):
    APPLICATION = 'application', 'Application'
    MESSAGE = 'message', 'Message'
    JOB = 'job', 'Job'
    SYSTEM = 'system', 'System'
    NEW_FOLLOWER = 'new_follower', 'New Follower'


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='Recipient of the notification'
    )
    title = models.CharField(max_length=255, default='HireSight Notification')
    message = models.TextField()
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    action_url = models.CharField(max_length=1024, blank=True, null=True)
    action_text = models.CharField(max_length=64, blank=True, null=True)
    related_object_id = models.CharField(max_length=64, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.email}"

    @property
    def type(self):
        return self.notification_type

    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @classmethod
    def unread_count(cls, user):
        """Return number of unread notifications for a user."""
        return cls.objects.filter(user=user, is_read=False).count()
