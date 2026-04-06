"""
Initialize translation strings in Python/Django files.
This should be run on all Python modules to extract translatable strings.
"""

from django.utils.translation import gettext_lazy as _

# Common translation strings for HireSight
# These serve as examples and reference for translation system

# Navigation and UI
COMMON_STRINGS = {
    'home': _('Home'),
    'dashboard': _('Dashboard'),
    'jobs': _('Jobs'),
    'applications': _('Applications'),
    'messages': _('Messages'),
    'settings': _('Settings'),
    'profile': _('Profile'),
    'logout': _('Logout'),
    'login': _('Login'),
    'register': _('Register'),
    'language': _('Language'),
    'select_language': _('Select Language'),
}

# Buttons and Actions
ACTION_STRINGS = {
    'submit': _('Submit'),
    'cancel': _('Cancel'),
    'save': _('Save'),
    'delete': _('Delete'),
    'edit': _('Edit'),
    'view': _('View'),
    'create': _('Create'),
    'update': _('Update'),
    'search': _('Search'),
    'filter': _('Filter'),
}

# Messages and Status
MESSAGE_STRINGS = {
    'loading': _('Loading...'),
    'success': _('Success'),
    'error': _('Error'),
    'warning': _('Warning'),
    'info': _('Information'),
    'required_fields': _('Please fill in all required fields'),
    'saved': _('Your settings have been saved'),
    'deleted': _('Item deleted successfully'),
    'updated': _('Item updated successfully'),
}

# Screening
SCREENING_STRINGS = {
    'screening': _('Screening'),
    'screening_questions': _('Screening Questions'),
    'create_screening': _('Create Screening'),
    'start_screening': _('Start Screening'),
    'screening_in_progress': _('Screening in Progress'),
    'screening_complete': _('Screening Complete'),
}

# Applications
APPLICATION_STRINGS = {
    'applications': _('Applications'),
    'new_application': _('New Application'),
    'view_application': _('View Application'),
    'application_status': _('Application Status'),
    'pending': _('Pending'),
    'reviewing': _('Reviewing'),
    'accepted': _('Accepted'),
    'rejected': _('Rejected'),
}

# AI Insights
AI_STRINGS = {
    'ai_insight': _('AI Insight'),
    'generate_insight': _('Generate Insight'),
    'insights': _('Insights'),
    'score': _('Score'),
    'recommendation': _('Recommendation'),
    'approve': _('Approve'),
    'reject': _('Reject'),
}

# Time-related strings
TIME_STRINGS = {
    'just_now': _('Just now'),
    'minutes_ago': _('%(minutes)d minutes ago'),
    'hours_ago': _('%(hours)d hours ago'),
    'days_ago': _('%(days)d days ago'),
    'weeks_ago': _('%(weeks)d weeks ago'),
    'months_ago': _('%(months)d months ago'),
}

# Email-related
EMAIL_STRINGS = {
    'email': _('Email'),
    'email_address': _('Email Address'),
    'email_sent': _('Email sent successfully'),
    'invalid_email': _('Invalid email address'),
    'email_verification': _('Email Verification'),
    'verify_email': _('Verify Email'),
}

# Validation
VALIDATION_STRINGS = {
    'required': _('This field is required'),
    'invalid': _('This field is invalid'),
    'min_length': _('This field must be at least %(min_length)d characters'),
    'max_length': _('This field must be at most %(max_length)d characters'),
    'email_invalid': _('Enter a valid email address'),
    'password_mismatch': _('Passwords do not match'),
}

# Account-related
ACCOUNT_STRINGS = {
    'account': _('Account'),
    'my_profile': _('My Profile'),
    'change_password': _('Change Password'),
    'current_password': _('Current Password'),
    'new_password': _('New Password'),
    'confirm_password': _('Confirm Password'),
    'password_changed': _('Password changed successfully'),
}
