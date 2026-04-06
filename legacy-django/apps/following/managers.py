from django.db import models
from django.db.models import Q, Exists, OuterRef, Count


class FollowQuerySet(models.QuerySet):
    """QuerySet that normalizes legacy lookups like `following` -> `followed`."""

    LEGACY_FIELD = 'following'
    LEGACY_FIELD_ID = 'following_id'
    LEGACY_PREFIX = f'{LEGACY_FIELD}__'
    TARGET_FIELD = 'followed'
    TARGET_FIELD_ID = f'{TARGET_FIELD}_id'
    TARGET_PREFIX = f'{TARGET_FIELD}__'

    def _normalize_kwargs(self, kwargs):
        if not kwargs:
            return {}

        normalized = {}
        for key, value in kwargs.items():
            if key == self.LEGACY_FIELD:
                normalized[self.TARGET_FIELD] = value
            elif key == self.LEGACY_FIELD_ID:
                normalized[self.TARGET_FIELD_ID] = value
            elif key.startswith(self.LEGACY_PREFIX):
                suffix = key[len(self.LEGACY_PREFIX):]
                normalized[f'{self.TARGET_PREFIX}{suffix}'] = value
            else:
                normalized[key] = value
        return normalized

    def _normalize_defaults(self, defaults):
        if not defaults:
            return defaults
        return self._normalize_kwargs(defaults)

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._normalize_kwargs(kwargs))

    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **self._normalize_kwargs(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._normalize_kwargs(kwargs))

    def create(self, **kwargs):
        return super().create(**self._normalize_kwargs(kwargs))

    def get_or_create(self, defaults=None, **kwargs):
        return super().get_or_create(
            defaults=self._normalize_defaults(defaults),
            **self._normalize_kwargs(kwargs)
        )

    def update_or_create(self, defaults=None, **kwargs):
        return super().update_or_create(
            defaults=self._normalize_defaults(defaults),
            **self._normalize_kwargs(kwargs)
        )

    def update(self, **kwargs):
        return super().update(**self._normalize_kwargs(kwargs))


class FollowManager(models.Manager):
    """
    Custom manager for Follow model with optimized queries.
    """
    use_in_migrations = True

    def get_queryset(self):
        return FollowQuerySet(self.model, using=self._db)

    def get_followers(self, user, annotate_mutual=False):
        """
        Get all users following the specified user.
        """
        queryset = self.filter(followed=user).select_related(
            'follower',
            'follower__personalprofile',
            'follower__companyprofile'
        )
        
        if annotate_mutual:
            queryset = queryset.annotate(
                is_mutual=Exists(
                    self.filter(
                        follower=user,
                        followed=OuterRef('follower')
                    )
                )
            )
        
        return queryset
    
    def get_following(self, user, annotate_mutual=False):
        """
        Get all users that the specified user is following.
        """
        queryset = self.filter(follower=user).select_related(
            'followed',
            'followed__personalprofile',
            'followed__companyprofile'
        )
        
        if annotate_mutual:
            queryset = queryset.annotate(
                is_mutual=Exists(
                    self.filter(
                        follower=OuterRef('followed'),
                        followed=user
                    )
                )
            )
        
        return queryset
    
    def get_mutual_followers(self, user1, user2):
        """
        Get users that both user1 and user2 follow.
        """
        user1_following = self.filter(follower=user1).values_list('followed_id', flat=True)
        user2_following = self.filter(follower=user2).values_list('followed_id', flat=True)
        
        from apps.accounts.models import User
        return User.objects.filter(
            id__in=set(user1_following) & set(user2_following)
        )
    
    def get_suggested_follows(self, user, limit=10):
        """
        Get suggested users to follow based on:
        - Users followed by people you follow
        - Users in same industry (if company)
        - Users with similar skills (if personal)
        """
        from apps.accounts.models import User
        
        # Get users already following
        already_following = self.filter(follower=user).values_list('followed_id', flat=True)
        
        # Get users followed by people you follow (2nd degree connections)
        second_degree = self.filter(
            follower__in=self.filter(follower=user).values_list('followed_id', flat=True)
        ).exclude(
            followed=user
        ).exclude(
            followed_id__in=already_following
        ).values('followed').annotate(
            common_count=Count('followed')
        ).order_by('-common_count')
        
        suggested_ids = [item['followed'] for item in second_degree[:limit]]
        
        return User.objects.filter(id__in=suggested_ids).select_related(
            'personalprofile',
            'companyprofile'
        )
    
    def get_follower_growth(self, user, days=30):
        """
        Get follower growth over specified number of days.
        Returns list of dicts with date and count.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        follows = self.filter(
            followed=user,
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return list(follows)

