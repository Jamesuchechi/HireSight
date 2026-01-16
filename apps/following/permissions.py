from rest_framework import permissions


class CanFollowPermission(permissions.BasePermission):
    """
    Permission to check if user can follow others.
    Only personal accounts can follow.
    """
    
    message = "Company accounts cannot follow users."
    
    def has_permission(self, request, view):
        # Allow read operations
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is personal account
        return request.user.account_type == 'personal'


class IsFollowerOrReadOnly(permissions.BasePermission):
    """
    Permission to check if user is the follower in a follow relationship.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the follower
        return obj.follower == request.user