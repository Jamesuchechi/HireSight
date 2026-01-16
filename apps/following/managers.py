from django.db import models
from django.db.models import Q, Exists, OuterRef, Count


class FollowManager(models.Manager):
    """
    Custom manager for Follow model with optimized queries.
    """
    
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


# Update the Follow model to use this manager
# Add this to models.py:
# objects = FollowManager()