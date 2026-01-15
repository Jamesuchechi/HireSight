"""
Application validators for business logic validation.
"""
from django.utils import timezone  # ✅ FIXED: Correct Django timezone import
from django.core.exceptions import ValidationError
from .models import ApplicationStatus


class InvalidStatusTransitionError(ValidationError):
    """Custom exception for invalid status transitions."""
    pass


# Define allowed status transitions
ALLOWED_TRANSITIONS = {
    ApplicationStatus.PENDING: [
        ApplicationStatus.SCREENING,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN
    ],
    ApplicationStatus.SCREENING: [
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN
    ],
    ApplicationStatus.INTERVIEW: [
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN
    ],
    ApplicationStatus.OFFER: [
        ApplicationStatus.HIRED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN
    ],
    ApplicationStatus.HIRED: [],  # Terminal state
    ApplicationStatus.REJECTED: [],  # Terminal state
    ApplicationStatus.WITHDRAWN: [],  # Terminal state
}


def validate_status_transition(old_status, new_status):
    """
    Validate that a status transition is allowed.
    
    Args:
        old_status: Current application status
        new_status: Proposed new status
        
    Raises:
        InvalidStatusTransitionError: If transition is not allowed
    """
    if old_status == new_status:
        return  # No change, always allowed
    
    allowed_transitions = ALLOWED_TRANSITIONS.get(old_status, [])
    
    if new_status not in allowed_transitions:
        raise InvalidStatusTransitionError(
            f"Cannot transition from {old_status} to {new_status}. "
            f"Allowed transitions: {', '.join(allowed_transitions) if allowed_transitions else 'None (terminal state)'}"
        )


def validate_application_ownership(application, user):
    """
    Validate that a user has permission to access an application.
    
    Args:
        application: Application instance
        user: User instance
        
    Raises:
        ValidationError: If user doesn't have permission
    """
    # Applicants can only access their own applications
    if user.account_type == 'personal':
        if application.applicant != user:
            raise ValidationError("You can only access your own applications.")
    
    # Company users can only access applications for their jobs
    elif user.account_type == 'company':
        if application.job.company.user != user:
            raise ValidationError("You can only access applications for your company's jobs.")
    
    else:
        raise ValidationError("Invalid account type.")


def validate_duplicate_application(job, applicant):
    """
    Validate that an applicant hasn't already applied to a job.
    
    Args:
        job: Job instance
        applicant: User instance (personal account)
        
    Raises:
        ValidationError: If duplicate application exists
    """
    from .models import Application
    
    if Application.objects.filter(job=job, applicant=applicant).exists():
        raise ValidationError("You have already applied to this job.")


def validate_job_application_eligibility(job, applicant):
    """
    Validate that a job is eligible for application.
    
    Args:
        job: Job instance
        applicant: User instance
        
    Raises:
        ValidationError: If job is not eligible for application
    """
    # Check job status
    if job.status != 'active':
        raise ValidationError("This job is not currently accepting applications.")
    
    # Check application deadline
    if job.application_deadline and job.application_deadline < timezone.now():
        raise ValidationError("The application deadline for this job has passed.")
    
    # Check email verification
    if not applicant.is_verified:
        raise ValidationError("You must verify your email before applying to jobs.")
    
    # Check if applicant has at least one resume
    if not applicant.resumes.exists():
        raise ValidationError("You must upload at least one resume before applying to jobs.")
    
    # Check if account is active
    if not applicant.is_active:
        raise ValidationError("Your account is not active. Please contact support.")


def validate_withdrawal_eligibility(application):
    """
    Validate that an application can be withdrawn.
    
    Args:
        application: Application instance
        
    Raises:
        ValidationError: If application cannot be withdrawn
    """
    if not application.can_withdraw:
        raise ValidationError(
            f"This application cannot be withdrawn in its current status: {application.get_status_display()}"
        )


def validate_application_update_permission(application, user):
    """
    Validate that a user can update an application.
    
    Args:
        application: Application instance
        user: User instance
        
    Raises:
        ValidationError: If user doesn't have permission
    """
    # Only company users can update applications
    if user.account_type != 'company':
        raise ValidationError("Only company users can update applications.")
    
    # Must be the company that posted the job
    if application.job.company.user != user:
        raise ValidationError("You can only update applications for your company's jobs.")


def validate_bulk_action_permission(applications, user):
    """
    Validate that a user can perform bulk actions on applications.
    
    Args:
        applications: Queryset of Application instances
        user: User instance
        
    Raises:
        ValidationError: If user doesn't have permission
    """
    # Only company users can perform bulk actions
    if user.account_type != 'company':
        raise ValidationError("Only company users can perform bulk actions.")
    
    # Verify all applications belong to user's company
    invalid_apps = applications.exclude(job__company__user=user)
    if invalid_apps.exists():
        raise ValidationError(
            f"You can only perform bulk actions on applications for your company's jobs. "
            f"Found {invalid_apps.count()} invalid applications."
        )


def validate_application_note_permission(application, user):
    """
    Validate that a user can add notes to an application.
    
    Args:
        application: Application instance
        user: User instance
        
    Raises:
        ValidationError: If user doesn't have permission
    """
    # Only company users can add notes
    if user.account_type != 'company':
        raise ValidationError("Only company users can add notes to applications.")
    
    # Must be the company that posted the job
    if application.job.company.user != user:
        raise ValidationError("You can only add notes to applications for your company's jobs.")