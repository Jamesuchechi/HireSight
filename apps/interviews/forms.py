from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from apps.applications.models import Application

from .models import Interview, InterviewFeedbackTemplate, InterviewPracticeSession


class InterviewScheduleForm(forms.ModelForm):
    """
    Form for scheduling a new interview
    Includes validation for date/time, required fields based on interview type
    """
    
    enable_live_coding = forms.BooleanField(
        required=False,
        label="Enable Live Coding Environment",
        help_text="Include a shared code editor for technical interviews."
    )

    class Meta:
        model = Interview
        fields = [
            'interview_type',
            'use_inapp_video',
            'enable_live_coding',  # Virtual field handled in view
            'scheduled_date',
            'duration_minutes',
            'timezone_name',
            'location',
            'video_link',
            'dial_in_number',
            'interviewer_name',
            'interviewer_email',
            'candidate_instructions',
            'company_notes',
        ]
        widgets = {
            'interview_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'required': True
            }),
            'use_inapp_video': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            }),
            'enable_live_coding': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'required': True
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': 15,
                'max': 480,
                'value': 60
            }),
            'timezone_name': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Office address or meeting room'
            }),
            'video_link': forms.URLInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'https://zoom.us/j/... or https://meet.google.com/...'
            }),
            'dial_in_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': '+1 234 567 8900'
            }),
            'interviewer_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'required': True
            }),
            'interviewer_email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'required': True
            }),
            'candidate_instructions': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Provide any specific instructions for the candidate...'
            }),
            'company_notes': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Internal notes (not visible to candidate)...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add common timezones
        common_timezones = [
            ('UTC', 'UTC'),
            ('America/New_York', 'Eastern Time (ET)'),
            ('America/Chicago', 'Central Time (CT)'),
            ('America/Denver', 'Mountain Time (MT)'),
            ('America/Los_Angeles', 'Pacific Time (PT)'),
            ('Europe/London', 'London (GMT/BST)'),
            ('Europe/Paris', 'Paris (CET/CEST)'),
            ('Asia/Tokyo', 'Tokyo (JST)'),
            ('Australia/Sydney', 'Sydney (AEST/AEDT)'),
        ]
        self.fields['timezone_name'].widget = forms.Select(
            choices=common_timezones,
            attrs=self.fields['timezone_name'].widget.attrs
        )
    
    def clean_scheduled_date(self):
        """Validate that interview is scheduled in the future"""
        scheduled_date = self.cleaned_data.get('scheduled_date')
        
        if scheduled_date:
            # Must be at least 1 hour in the future
            min_schedule_time = timezone.now() + timedelta(hours=1)
            if scheduled_date < min_schedule_time:
                raise ValidationError(
                    'Interview must be scheduled at least 1 hour in the future.'
                )
            
            # Don't schedule more than 1 year in advance
            max_schedule_time = timezone.now() + timedelta(days=365)
            if scheduled_date > max_schedule_time:
                raise ValidationError(
                    'Interview cannot be scheduled more than 1 year in advance.'
                )
        
        return scheduled_date
    
    def clean(self):
        """Additional validation based on interview type"""
        cleaned_data = super().clean()
        interview_type = cleaned_data.get('interview_type')
        video_link = cleaned_data.get('video_link')
        location = cleaned_data.get('location')
        
        if interview_type == Interview.InterviewType.VIDEO:
            use_inapp = cleaned_data.get('use_inapp_video')
            if not video_link and not use_inapp:
                self.add_error('video_link', 'Please provide a video link OR select "Use HireSight built-in video conferencing".')
        
        # Require location for on-site interviews
        if interview_type == Interview.InterviewType.ONSITE:
            if not location:
                self.add_error('location', 'Physical location is required for on-site interviews.')
        
        return cleaned_data


class InterviewRescheduleForm(forms.Form):
    """
    Form for rescheduling an existing interview
    """
    
    new_scheduled_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'required': True
        }),
        label='New Date & Time',
        help_text='Select a new date and time for the interview'
    )
    
    reschedule_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Please provide a reason for rescheduling...'
        }),
        label='Reason for Rescheduling',
        required=True,
        help_text='This will be shared with the candidate'
    )
    
    def __init__(self, *args, interview=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.interview = interview

    def clean_new_scheduled_date(self):
        """Validate new scheduled date"""
        new_date = self.cleaned_data.get('new_scheduled_date')
        
        if new_date:
            # Must be at least 1 hour in the future
            min_schedule_time = timezone.now() + timedelta(hours=1)
            if new_date < min_schedule_time:
                raise ValidationError(
                    'New interview time must be at least 1 hour in the future.'
                )
            
            # Don't schedule more than 1 year in advance
            max_schedule_time = timezone.now() + timedelta(days=365)
            if new_date > max_schedule_time:
                raise ValidationError(
                    'Interview cannot be scheduled more than 1 year in advance.'
                )
            
            if self.interview:
                new_end = new_date + timedelta(minutes=self.interview.duration_minutes)
                conflicts = Interview.objects.filter(
                    Q(application__applicant=self.interview.application.applicant) |
                    Q(application__job__company=self.interview.application.job.company)
                ).exclude(pk=self.interview.pk).distinct()

                for existing in conflicts:
                    existing_end = existing.scheduled_date + timedelta(minutes=existing.duration_minutes)
                    if new_date < existing_end and new_end > existing.scheduled_date:
                        raise ValidationError(
                            'This new time conflicts with another interview already scheduled for the candidate or company.'
                        )
        
        return new_date


class InterviewCancelForm(forms.Form):
    """
    Form for cancelling an interview
    """
    
    cancellation_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500',
            'rows': 4,
            'placeholder': 'Please provide a reason for cancellation...'
        }),
        label='Reason for Cancellation',
        required=True,
        help_text='This will be shared with the other party'
    )
    
    confirm_cancellation = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'
        }),
        label='I confirm that I want to cancel this interview',
        required=True,
        help_text='This action cannot be undone'
    )


class InterviewCompleteForm(forms.Form):
    """
    Form for marking an interview as completed and adding feedback
    """

    template = forms.ModelChoiceField(
        queryset=InterviewFeedbackTemplate.objects.none(),
        required=False,
        label='Feedback Template',
        help_text='Optional pre-built feedback template'
    )

    completion_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'rows': 5,
            'placeholder': 'Add notes about how the interview went...'
        }),
        label='Completion Notes',
        required=False,
        help_text='Internal notes about the interview'
    )

    interview_rating = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'min': 1,
            'max': 5
        }),
        label='Overall Rating',
        required=False,
        min_value=1,
        max_value=5,
        help_text='Rate the candidate from 1 (poor) to 5 (excellent)'
    )

    interviewer_feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'rows': 6,
            'placeholder': 'Detailed feedback about the candidate...'
        }),
        label='Detailed Feedback',
        required=False,
        help_text='Detailed assessment of the candidate'
    )

    recommend_next_round = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        }),
        label='Recommend for next round',
        required=False
    )

    def __init__(self, *args, company_user=None, interview_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company_user and interview_type:
            self.fields['template'].queryset = InterviewFeedbackTemplate.objects.filter(
                company=company_user,
                interview_type=interview_type
            )
        else:
            self.fields['template'].queryset = InterviewFeedbackTemplate.objects.none()


class InterviewNoShowForm(forms.Form):
    """
    Form for marking a candidate as no-show
    """
    
    no_show_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-yellow-500 focus:ring-yellow-500',
            'rows': 3,
            'placeholder': 'Add any relevant notes...'
        }),
        label='Notes',
        required=False,
        help_text='Any additional context about the no-show'
    )
    
    contacted_candidate = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-yellow-600 focus:ring-yellow-500'
        }),
        label='I have attempted to contact the candidate',
        required=True,
        help_text='Confirm you tried to reach the candidate before marking as no-show'
    )


class BulkInterviewActionForm(forms.Form):
    """
    Form for bulk actions on interviews
    """
    
    ACTION_CHOICES = [
        ('', 'Select an action...'),
        ('cancel', 'Cancel selected interviews'),
        ('export', 'Export to calendar'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        label='Action',
        required=True
    )
    
    interview_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )


class InterviewResponseForm(forms.Form):
    """
    Form for candidates to respond to interview invitations
    """
    
    ACTION_CHOICES = [
        ('accept', 'Accept'),
        ('decline', 'Decline'),
        ('propose_reschedule', 'Propose new time'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(),
        label='Response',
        required=True
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional note'
        }),
        label='Reason',
        required=False
    )
    proposed_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'mt-1 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        label='Proposed Date & Time',
        required=False,
        help_text='Only required when proposing a new time'
    )

    def clean(self):
        cleaned = super().clean()
        action = cleaned.get('action')
        reason = cleaned.get('reason')
        proposed_date = cleaned.get('proposed_date')

        if action == 'decline' and not reason:
            self.add_error('reason', 'Please let us know why you are declining.')
        if action == 'propose_reschedule':
            if not proposed_date:
                self.add_error('proposed_date', 'Please select a new date and time.')
            if not reason:
                self.add_error('reason', 'Please tell us why you need to reschedule.')

        return cleaned


class PracticeSessionForm(forms.ModelForm):
    """Form for candidates to create a practice session."""

    class Meta:
        model = InterviewPracticeSession
        fields = ['application', 'interview_type', 'difficulty', 'focus_area', 'enable_video', 'settings']
        widgets = {
            'interview_type': forms.Select(attrs={'class': 'mt-1 block w-full'}),
            'difficulty': forms.Select(choices=[
                ('Beginner', 'Beginner'),
                ('Intermediate', 'Intermediate'),
                ('Advanced', 'Advanced'),
            ], attrs={'class': 'mt-1 block w-full'}),
            'focus_area': forms.TextInput(attrs={'class': 'mt-1 block w-full'}),
            'settings': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full'}),
        }

    def __init__(self, *args, candidate=None, **kwargs):
        super().__init__(*args, **kwargs)
        if candidate:
            self.fields['application'].queryset = Application.objects.filter(applicant=candidate)
        else:
            self.fields['application'].queryset = Application.objects.none()

    def clean(self):
        cleaned = super().clean()
        settings_raw = self.data.get('settings', '')
        if cleaned.get('enable_video') and not settings_raw.strip():
            self.add_error('settings', 'Please describe how video will be used in the session.')
        return cleaned

    def clean_settings(self):
        data = self.cleaned_data.get('settings')
        if not data:
            return {}
        return data


class PracticeResponseForm(forms.Form):
    """Form for submitting a practice question response."""

    text_response = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'class': 'mt-1 block w-full rounded-md border-gray-300'
        }),
        required=False
    )
    video_url = forms.URLField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300'})
    )
    video_analysis_metrics = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
