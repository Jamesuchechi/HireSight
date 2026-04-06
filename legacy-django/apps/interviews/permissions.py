from django.core.exceptions import PermissionDenied


def user_can_schedule_interview(user, application):
    """
    Check if user can schedule an interview for an application
    
    Args:
        user: User instance
        application: Application instance
    
    Returns:
        bool: True if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    if user.account_type != 'company':
        raise PermissionDenied("Only company accounts can schedule interviews")
    
    if application.job.company.user != user:
        raise PermissionDenied("You can only schedule interviews for your own job postings")
    
    return True


def user_can_access_interview(user, interview):
    """
    Check if user can access an interview
    
    Args:
        user: User instance
        interview: Interview instance
    
    Returns:
        bool: True if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    # Company can access if they own the job
    if user.account_type == 'company':
        if interview.application.job.company.user == user:
            return True
    
    # Candidate can access if it's their application
    elif user.account_type == 'personal':
        if interview.application.applicant == user:
            return True
    
    raise PermissionDenied("You don't have permission to access this interview")


def user_can_reschedule_interview(user, interview):
    """
    Check if user can reschedule an interview
    
    Args:
        user: User instance
        interview: Interview instance
    
    Returns:
        bool: True if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    # First check if user can access
    user_can_access_interview(user, interview)
    
    # Check if interview can be rescheduled
    if not interview.can_reschedule():
        raise PermissionDenied("This interview cannot be rescheduled")
    
    return True


def user_can_cancel_interview(user, interview):
    """
    Check if user can cancel an interview
    
    Args:
        user: User instance
        interview: Interview instance
    
    Returns:
        bool: True if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    # First check if user can access
    user_can_access_interview(user, interview)
    
    # Check if interview can be cancelled
    if not interview.can_cancel():
        raise PermissionDenied("This interview cannot be cancelled")
    
    return True


def user_can_mark_interview_completed(user, interview):
    """
    Check if user can mark an interview as completed
    Only company users can mark interviews as completed
    
    Args:
        user: User instance
        interview: Interview instance
    
    Returns:
        bool: True if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    if user.account_type != 'company':
        raise PermissionDenied("Only company accounts can mark interviews as completed")
    
    if interview.application.job.company.user != user:
        raise PermissionDenied("You can only complete interviews for your own job postings")
    
    if not interview.can_mark_completed():
        raise PermissionDenied("This interview cannot be marked as completed yet")
    
    return True


def user_can_mark_no_show(user, interview):
    """
    Check if user can mark a candidate as no-show
    Only company users can mark no-shows
    
    Args:
        user: User instance
        interview: Interview instance
    
    Returns:
        bool: True if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    if user.account_type != 'company':
        raise PermissionDenied("Only company accounts can mark candidates as no-show")
    
    if interview.application.job.company.user != user:
        raise PermissionDenied("You can only mark no-shows for your own interviews")
    
    from django.utils import timezone
    if interview.scheduled_date > timezone.now():
        raise PermissionDenied("Cannot mark as no-show before interview time")
    
    return True