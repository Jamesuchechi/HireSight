from django.utils.functional import SimpleLazyObject
from .models import Follow


def get_follow_counts(request):
    """Get follow counts for the current user"""
    if not request.user.is_authenticated:
        return {'follower_count': 0, 'following_count': 0}
    
    return {
        'follower_count': Follow.get_follower_count(request.user),
        'following_count': Follow.get_following_count(request.user),
    }


class FollowCountMiddleware:
    """
    Middleware to add follow counts to every request.
    Makes follower/following counts available in all templates.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.follow_counts = SimpleLazyObject(lambda: get_follow_counts(request))
        response = self.get_response(request)
        return response