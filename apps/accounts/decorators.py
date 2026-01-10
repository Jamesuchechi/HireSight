from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def personal_required(view_func):
    """
    Decorator for views that require a Personal (Job Seeker) account.
    Redirects Company accounts or shows 403 error.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if request.user.account_type != 'personal':
            messages.error(request, 'This page is only accessible to Job Seeker accounts.')
            return redirect('dashboard:index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def company_required(view_func):
    """
    Decorator for views that require a Company (Recruiter) account.
    Redirects Personal accounts or shows 403 error.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if request.user.account_type != 'company':
            messages.error(request, 'This page is only accessible to Recruiter accounts.')
            return redirect('dashboard:index')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def verified_required(view_func):
    """
    Decorator for views that require email verification.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if not request.user.is_verified:
            messages.warning(request, 'Please verify your email address to access this page.')
            return redirect('accounts:verify_email_notice')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def verified_company_required(view_func):
    """
    Decorator for views that require a verified company account.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if request.user.account_type != 'company':
            messages.error(request, 'This page is only accessible to Recruiter accounts.')
            return redirect('dashboard:index')
        
        if not hasattr(request.user, 'company_profile') or not request.user.company_profile.is_verified():
            messages.warning(request, 'Your company needs to be verified to access this feature.')
            return redirect('accounts:profile')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper