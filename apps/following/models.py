from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from apps.accounts.models import User

from .managers import FollowManager


class Follow(models.Model):
    """
    Represents a follow relationship between users.
    Personal accounts can follow both companies and other personal accounts.
    Companies cannot follow anyone.
    """
    objects = FollowManager()
    follower = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='following',
        help_text="User who is following"
    )
    followed = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='followers',
        help_text="User being followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Track notification sent status
    notification_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ('follower', 'followed')
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['followed', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.email} follows {self.followed.email}"

    @property
    def following(self):
        """Alias for the entity being followed (kept for legacy code)."""
        return self.followed

    @property
    def following_type(self):
        """Return the followed user's account type for optional analytics metadata."""
        return 'company' if self.followed.account_type == 'company' else 'user'

    def clean(self):
        """Validation: Users cannot follow themselves, companies cannot follow"""
        from django.core.exceptions import ValidationError
        
        if self.follower == self.followed:
            raise ValidationError("Users cannot follow themselves")
        
        if self.follower.account_type == 'company':
            raise ValidationError("Company accounts cannot follow users")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_mutual_followers(cls, user1, user2):
        """Get users that both user1 and user2 follow"""
        user1_following = cls.objects.filter(follower=user1).values_list('followed', flat=True)
        user2_following = cls.objects.filter(follower=user2).values_list('followed', flat=True)
        mutual_ids = set(user1_following) & set(user2_following)
        return User.objects.filter(id__in=mutual_ids).annotate(followers_count=Count('followers'))

    @classmethod
    def are_mutual_followers(cls, user1, user2):
        """Check if two users follow each other"""
        return (
            cls.objects.filter(follower=user1, followed=user2).exists() and
            cls.objects.filter(follower=user2, followed=user1).exists()
        )

    @classmethod
    def get_follower_count(cls, user):
        """Get count of users following this user"""
        return cls.objects.filter(followed=user).count()

    @classmethod
    def get_following_count(cls, user):
        """Get count of users this user is following"""
        return cls.objects.filter(follower=user).count()


class ActivityType(models.TextChoices):
    JOB_POSTED = 'job_posted', 'Job Posted'
    PROFILE_UPDATED = 'profile_updated', 'Profile Updated'
    SKILL_ADDED = 'skill_added', 'Skill Added'
    FOLLOWED_USER = 'followed_user', 'Followed User'
    UNFOLLOWED_USER = 'unfollowed_user', 'Unfollowed User'
    BULK_OPERATION = 'bulk_operation', 'Bulk Follow Operation'


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=32, choices=ActivityType.choices)
    content = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()}"

    def get_profile_url(self):
        return reverse('accounts:profile_detail', kwargs={'user_id': self.user.id})
