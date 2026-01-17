from django import forms

from .models import Interview


class InterviewScheduleForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = [
            'interview_type',
            'scheduled_date',
            'duration_minutes',
            'location',
            'video_link',
            'dial_in_number',
            'interviewer_name',
            'interviewer_email',
            'candidate_instructions',
        ]
        widgets = {
            'interview_type': forms.Select(attrs={'class': 'form-select w-full'}),
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input w-full'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-input w-full', 'value': 60}),
            'location': forms.TextInput(attrs={'class': 'form-input w-full'}),
            'video_link': forms.URLInput(attrs={'class': 'form-input w-full', 'placeholder': 'https://zoom.us/j/...'}),
            'dial_in_number': forms.TextInput(attrs={'class': 'form-input w-full'}),
            'interviewer_name': forms.TextInput(attrs={'class': 'form-input w-full'}),
            'interviewer_email': forms.EmailInput(attrs={'class': 'form-input w-full'}),
            'candidate_instructions': forms.Textarea(attrs={'class': 'form-textarea w-full', 'rows': 4}),
        }


class InterviewRescheduleForm(forms.Form):
    new_scheduled_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input w-full'}),
        label='New Date & Time'
    )


class InterviewCancelForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-textarea w-full', 'rows': 3}),
        label='Reason for Cancellation',
        required=True
    )
