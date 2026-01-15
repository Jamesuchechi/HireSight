# apps/messages/forms.py
from django import forms
from .models import Message, MessageTemplate, MessageReport, Conversation
from apps.accounts.models import User


class ComposeMessageForm(forms.ModelForm):
    """
    Form for composing a new message/conversation
    """
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Select recipient'
        }),
        help_text="Select the person you want to message"
    )
    
    subject = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Subject (optional)'
        })
    )
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Type your message here...',
            'rows': 6
        }),
        help_text="Enter your message"
    )

    class Meta:
        model = Message
        fields = ['content']

    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        super().__init__(*args, **kwargs)
        
        # Exclude blocked users and the sender from recipient choices
        if self.sender:
            blocked_ids = self.sender.blocked_users.values_list('blocked_id', flat=True)
            blocked_by_ids = self.sender.blocked_by.values_list('blocker_id', flat=True)
            excluded_ids = list(blocked_ids) + list(blocked_by_ids) + [self.sender.id]
            self.fields['recipient'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id__in=excluded_ids)

    def clean_recipient(self):
        recipient = self.cleaned_data.get('recipient')
        if recipient == self.sender:
            raise forms.ValidationError("You cannot send a message to yourself.")
        return recipient


class ReplyMessageForm(forms.ModelForm):
    """
    Form for replying to an existing conversation
    """
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Type your reply...',
            'rows': 4
        }),
        label='',
        help_text="Press Ctrl+Enter to send"
    )
    
    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'id': 'file-upload',
            'accept': 'image/*,application/pdf,.doc,.docx'
        }),
        help_text="Optional: Attach an image or PDF (max 5MB)"
    )

    class Meta:
        model = Message
        fields = ['content']

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Check file size (5MB limit)
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 5MB")
            
            # Check file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            if attachment.content_type not in allowed_types:
                raise forms.ValidationError("Only images, PDFs, and Word documents are allowed")
        
        return attachment


class MessageTemplateForm(forms.ModelForm):
    """
    Form for creating/editing message templates (company users only)
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., Interview Invitation'
        })
    )
    
    subject = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Subject line for the message'
        })
    )
    
    category = forms.ChoiceField(
        choices=MessageTemplate.TEMPLATE_CATEGORIES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Template message content. Use {name} for candidate name, {job_title} for position, etc.',
            'rows': 8
        }),
        help_text="You can use placeholders like {name}, {job_title}, {company_name}"
    )

    class Meta:
        model = MessageTemplate
        fields = ['name', 'subject', 'category', 'content', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            })
        }


class MessageReportForm(forms.ModelForm):
    """
    Form for reporting inappropriate messages
    """
    reason = forms.ChoiceField(
        choices=MessageReport.REPORT_REASONS,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
            'placeholder': 'Please provide additional details (optional)',
            'rows': 4
        })
    )

    class Meta:
        model = MessageReport
        fields = ['reason', 'description']


class SearchMessagesForm(forms.Form):
    """
    Form for searching messages and conversations
    """
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Search messages, people, or content...',
            'type': 'search'
        })
    )
    
    filter_type = forms.ChoiceField(
        required=False,
        choices=[
            ('all', 'All Messages'),
            ('unread', 'Unread'),
            ('archived', 'Archived'),
        ],
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )