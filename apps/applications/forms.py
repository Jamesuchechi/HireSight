"""
Application forms for job applications.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Application, ApplicationNote, ApplicationStatus
from .validators import (
    validate_duplicate_application,
    validate_job_application_eligibility,
    validate_withdrawal_eligibility
)


class ApplicationForm(forms.ModelForm):
    """Form for job seekers to apply for a job."""

    class Meta:
        model = Application
        fields = ['resume', 'cover_letter', 'portfolio_url', 'screening_answers', 'additional_notes']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Tell us why you\'re a great fit for this role...',
                'id': 'id_cover_letter'  # Ensure consistent ID for TinyMCE
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'https://your-portfolio.com'
            }),
            'additional_notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Any additional information you\'d like to share...'
            }),
        }
        labels = {
            'resume': 'Select Resume',
            'cover_letter': 'Cover Letter',
            'portfolio_url': 'Portfolio URL (Optional)',
            'screening_answers': 'Screening Questions',
            'additional_notes': 'Additional Notes (Optional)',
        }
        help_texts = {
            'resume': 'Choose which version of your resume to submit',
            'cover_letter': 'Required if specified by the employer',
            'portfolio_url': 'Link to your online portfolio or personal website',
        }

    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job', None)
        self.applicant = kwargs.pop('applicant', None)
        super().__init__(*args, **kwargs)
        
        # Set resume choices to applicant's resumes
        if self.applicant:
            self.fields['resume'].queryset = self.applicant.resumes.all()
            self.fields['resume'].empty_label = "Select a resume"
            
            # Set primary resume as initial value
            primary_resume = self.applicant.resumes.filter(is_primary=True).first()
            if primary_resume:
                self.initial['resume'] = primary_resume
        
        # Make fields required based on job requirements
        if self.job:
            if self.job.requires_cover_letter:
                self.fields['cover_letter'].required = True
                self.fields['cover_letter'].widget.attrs['class'] += ' required'
            
            if self.job.requires_portfolio:
                self.fields['portfolio_url'].required = True
                self.fields['portfolio_url'].widget.attrs['class'] += ' required'

    def clean(self):
        """Validate the application form."""
        cleaned_data = super().clean()
        
        # Validate job and applicant are provided
        if not self.job:
            raise ValidationError("Job is required.")
        
        if not self.applicant:
            raise ValidationError("Applicant is required.")
        
        # Validate job eligibility
        validate_job_application_eligibility(self.job, self.applicant)
        
        # Validate no duplicate application
        validate_duplicate_application(self.job, self.applicant)
        
        # Validate required fields based on job requirements
        if self.job.requires_cover_letter and not cleaned_data.get('cover_letter'):
            self.add_error('cover_letter', 'Cover letter is required for this job.')
        
        if self.job.requires_portfolio and not cleaned_data.get('portfolio_url'):
            self.add_error('portfolio_url', 'Portfolio URL is required for this job.')
        
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        """Save the application with additional data."""
        application = super().save(commit=False)
        application.job = self.job
        application.applicant = self.applicant
        
        if commit:
            application.save()
            
            # ✅ FIXED: Create initial status history with None as old_status
            from .models import ApplicationStatusHistory
            ApplicationStatusHistory.objects.create(
                application=application,
                old_status=None,  # ✅ First status change, no previous status
                new_status=application.status,
                changed_by=self.applicant,
                notes="Application submitted"
            )
        
        return application


class ApplicationReviewForm(forms.ModelForm):
    """Form for companies to review and update application status."""

    class Meta:
        model = Application
        fields = ['status', 'recruiter_notes', 'rating', 'is_shortlisted', 'tags']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'recruiter_notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Add internal notes about this candidate...'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }, choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)]),
            'is_shortlisted': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-blue-600 focus:ring-blue-500'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Add tags (comma-separated)'
            }),
        }
        labels = {
            'status': 'Application Status',
            'recruiter_notes': 'Internal Notes',
            'rating': 'Candidate Rating',
            'is_shortlisted': 'Add to Shortlist',
            'tags': 'Tags',
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Customize rating field
        self.fields['rating'].required = False
        self.fields['rating'].empty_label = "No rating"

    def clean_status(self):
        """Validate status transition."""
        new_status = self.cleaned_data.get('status')
        
        # Only validate if instance exists and status is changing
        if self.instance and self.instance.pk:
            old_status = self.instance.status
            
            if old_status != new_status:
                from .validators import validate_status_transition
                validate_status_transition(old_status, new_status)
        
        return new_status
    
    def clean_tags(self):
        """Convert comma-separated tags to list."""
        tags = self.cleaned_data.get('tags', '')
        
        if isinstance(tags, str):
            # Split by comma and clean each tag
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            return tag_list
        
        return tags

    @transaction.atomic
    def save(self, commit=True):
        """Save the application review with status history."""
        application = super().save(commit=False)
        
        # Store old status before saving
        old_status = None
        if self.instance.pk:
            old_status = Application.objects.get(pk=self.instance.pk).status
        
        if commit:
            application.save()
            
            # Create status history if status changed
            if old_status and old_status != application.status:
                from .models import ApplicationStatusHistory
                ApplicationStatusHistory.objects.create(
                    application=application,
                    old_status=old_status,
                    new_status=application.status,
                    changed_by=self.current_user,
                    notes=f"Status updated via review form"
                )
        
        return application


class ApplicationFilterForm(forms.Form):
    """Form for filtering applications."""

    STATUS_CHOICES = [
        ('', 'All Statuses'),
    ] + [(status.value, status.label) for status in ApplicationStatus]
    
    RATING_CHOICES = [
        ('', 'Any Rating'),
        ('5', '5 Stars'),
        ('4', '4+ Stars'),
        ('3', '3+ Stars'),
        ('2', '2+ Stars'),
        ('1', '1+ Stars'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select rounded-md border-gray-300'})
    )
    
    match_score_min = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'Min score'
        })
    )
    
    match_score_max = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'Max score'
        })
    )
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select rounded-md border-gray-300'})
    )
    
    is_shortlisted = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-blue-600'})
    )
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'Search candidates...'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'type': 'date'
        })
    )
    
    # Add job-specific filtering
    job_id = forms.UUIDField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    # Add tags filtering
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'Filter by tags (comma-separated)'
        })
    )
    
    def clean(self):
        """Validate filter form."""
        cleaned_data = super().clean()
        
        # Validate score range
        min_score = cleaned_data.get('match_score_min')
        max_score = cleaned_data.get('match_score_max')
        
        if min_score is not None and max_score is not None and min_score > max_score:
            raise ValidationError("Minimum score cannot be greater than maximum score.")
        
        # Validate date range
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class ApplicationBulkActionForm(forms.Form):
    """Form for bulk actions on applications."""

    ACTION_CHOICES = [
        ('', 'Select action...'),
        ('shortlist', 'Add to Shortlist'),
        ('unshortlist', 'Remove from Shortlist'),
        ('status', 'Change Status'),
        ('rating', 'Set Rating'),
        ('tag', 'Add Tag'),
        ('remove_tag', 'Remove Tag'),
        ('export', 'Export Selected'),
        ('delete', 'Delete Applications'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select rounded-md border-gray-300'})
    )
    
    new_status = forms.ChoiceField(
        choices=[(status.value, status.label) for status in ApplicationStatus],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select rounded-md border-gray-300'})
    )
    
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select rounded-md border-gray-300'})
    )
    
    tag = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'Enter tag'
        })
    )
    
    confirm = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-blue-600'})
    )
    
    def clean(self):
        """Validate bulk action form."""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        # Validate required fields based on action
        if action == 'status' and not cleaned_data.get('new_status'):
            self.add_error('new_status', 'New status is required for status change.')
        
        if action == 'rating' and not cleaned_data.get('rating'):
            self.add_error('rating', 'Rating is required for rating action.')
        
        if action in ['tag', 'remove_tag'] and not cleaned_data.get('tag'):
            self.add_error('tag', 'Tag is required for tagging action.')
        
        if action == 'delete' and not cleaned_data.get('confirm'):
            self.add_error('confirm', 'Please confirm deletion.')
        
        return cleaned_data


class ApplicationNoteForm(forms.ModelForm):
    """Form for adding notes to applications."""

    class Meta:
        model = ApplicationNote
        fields = ['note', 'is_important']
        widgets = {
            'note': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Add a note about this candidate...'
            }),
            'is_important': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-blue-600 focus:ring-blue-500'
            }),
        }
        labels = {
            'note': 'Note',
            'is_important': 'Mark as Important',
        }

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        self.author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def save(self, commit=True):
        """Save the note with application and author."""
        note = super().save(commit=False)
        note.application = self.application
        note.author = self.author
        
        if commit:
            note.save()
        
        return note


class ApplicationWithdrawForm(forms.Form):
    """Form for applicants to withdraw their application."""

    confirmation = forms.BooleanField(
        required=True,
        label="I confirm that I want to withdraw this application",
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-red-600'})
    )
    
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Optional: Please tell us why you\'re withdrawing...'
        }),
        label="Reason for withdrawal (optional)"
    )

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate withdrawal form."""
        cleaned_data = super().clean()
        
        # Validate application can be withdrawn
        if self.application:
            validate_withdrawal_eligibility(self.application)
        
        return cleaned_data

    @transaction.atomic
    def save(self):
        """Withdraw the application."""
        if self.application:
            from .models import ApplicationStatusHistory
            
            old_status = self.application.status
            self.application.status = ApplicationStatus.WITHDRAWN
            self.application.save()
            
            # Create status history
            ApplicationStatusHistory.objects.create(
                application=self.application,
                old_status=old_status,
                new_status=self.application.status,
                changed_by=self.application.applicant,
                reason=self.cleaned_data.get('reason', ''),
                notes="Application withdrawn by applicant"
            )
            
            return self.application
        
        return None


class ApplicationRejectionForm(forms.Form):
    """Form for companies to provide feedback when rejecting applications."""

    REJECTION_REASONS = [
        ('experience', 'Insufficient Experience'),
        ('skills', 'Skills Not Matching'),
        ('education', 'Education Requirements Not Met'),
        ('location', 'Location Preferences'),
        ('salary', 'Salary Expectations'),
        ('culture', 'Cultural Fit'),
        ('timing', 'Timing Issues'),
        ('other', 'Other'),
    ]

    rejection_reason = forms.ChoiceField(
        choices=REJECTION_REASONS,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500'
        }),
        label="Primary Reason for Rejection"
    )

    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Provide constructive feedback to help the candidate improve...'
        }),
        label="Feedback (Optional)",
        help_text="This feedback will be shared with the applicant to help them improve."
    )

    internal_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Internal notes for your team...'
        }),
        label="Internal Notes (Optional)"
    )

    notify_applicant = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox rounded text-blue-600 focus:ring-blue-500'
        }),
        label="Send rejection email to applicant",
        help_text="Uncheck if you prefer not to notify the applicant at this time."
    )

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate rejection form."""
        cleaned_data = super().clean()

        # If feedback is provided but notification is disabled, warn
        if cleaned_data.get('feedback') and not cleaned_data.get('notify_applicant'):
            self.add_error('notify_applicant', 'Feedback will not be sent if notification is disabled.')

        return cleaned_data

    @transaction.atomic
    def save(self):
        """Process the rejection with feedback."""
        if not self.application:
            return None

        from .models import ApplicationStatusHistory

        # Update application status
        old_status = self.application.status
        self.application.status = ApplicationStatus.REJECTED
        self.application.save()

        # Create status history with rejection details
        rejection_details = {
            'reason': self.cleaned_data['rejection_reason'],
            'feedback': self.cleaned_data.get('feedback', ''),
            'internal_notes': self.cleaned_data.get('internal_notes', ''),
            'notify_applicant': self.cleaned_data.get('notify_applicant', True)
        }

        ApplicationStatusHistory.objects.create(
            application=self.application,
            old_status=old_status,
            new_status=self.application.status,
            changed_by=self.cleaned_data.get('changed_by'),
            reason=f"Rejected: {dict(self.REJECTION_REASONS)[self.cleaned_data['rejection_reason']]}",
            notes=self.cleaned_data.get('internal_notes', '')
        )

        # Store rejection feedback in application for email
        self.application.rejection_feedback = rejection_details
        self.application.save(update_fields=['rejection_feedback'])

        return self.application