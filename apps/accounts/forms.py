from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, PersonalProfile, CompanyProfile, EmailPreferences
import json

class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads."""
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class RegisterForm(UserCreationForm):
    """Form for user registration with email and account type."""
    
    email = forms.EmailField(
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email'
        })
    )
    
    account_type = forms.ChoiceField(
        choices=User.ACCOUNT_TYPE_CHOICES,
        required=True,
        initial='personal',
        widget=forms.RadioSelect(attrs={
            'class': 'focus:ring-blue'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue'
        }),
        error_messages={
            'required': 'You must accept the Terms of Service and Privacy Policy.'
        }
    )
    
    class Meta:
        model = User
        fields = ['email', 'account_type', 'password1', 'password2']
    
    def clean_email(self):
        """Validate that email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('This email address is already registered.')
        return email.lower()
    
    def save(self, commit=True):
        """Save user with lowercased email."""
        user = super().save(commit=False)
        user.email = user.email.lower()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Form for user login with email."""
    
    username = forms.EmailField(
        label='Email',
        max_length=255,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email'
        })
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue'
        })
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """Override to skip authentication - we'll handle it in the view."""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Don't authenticate here - let the view handle it
            pass

        return self.cleaned_data


class EmailVerificationForm(forms.Form):
    """Form for email verification token."""
    
    token = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl text-center font-mono tracking-wider focus:ring-2 focus:ring-blue focus:border-blue transition uppercase',
            'placeholder': 'ENTER-TOKEN-HERE',
            'autocomplete': 'off'
        })
    )


class ForgotPasswordForm(PasswordResetForm):
    """Form for requesting password reset."""
    
    email = forms.EmailField(
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email'
        })
    )


class ResetPasswordForm(SetPasswordForm):
    """Form for setting new password."""
    
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )
    
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )

class PersonalProfileForm(forms.ModelForm):
    """Form for editing personal (job seeker) profile."""
    
    class Meta:
        model = PersonalProfile
        fields = [
            'full_name',
            'headline',
            'avatar',
            'location',
            'phone',
            'bio',
            'preferred_job_types',
            'remote_preference',
            'salary_expectation_min',
            'salary_expectation_max',
            'salary_currency',
            'availability',
            'profile_visibility'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'John Doe'
            }),
            'headline': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Senior React Developer'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
                'accept': 'image/*'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'San Francisco, CA'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': '+1 (555) 123-4567'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Tell us about yourself...',
                'rows': 4
            }),
            'salary_expectation_min': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': '80000'
            }),
            'salary_expectation_max': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': '120000'
            }),
            'salary_currency': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
            }),
            'availability': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
            }),
            'profile_visibility': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
            }),
            'remote_preference': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
            }),
        }

    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
        
       # Make salary_currency optional
       self.fields['salary_currency'].required = False
        
       # Add currency choices
       self.fields['salary_currency'].widget = forms.Select(
           choices=[
               ('', 'Select Currency'),
               ('USD', 'USD - US Dollar'),
               ('EUR', 'EUR - Euro'),
               ('GBP', 'GBP - British Pound'),
               ('NGN', 'NGN - Nigerian Naira'),
               ('CAD', 'CAD - Canadian Dollar'),
               ('AUD', 'AUD - Australian Dollar'),
               ('JPY', 'JPY - Japanese Yen'),
               ('CNY', 'CNY - Chinese Yuan'),
               ('INR', 'INR - Indian Rupee'),
           ],
           attrs={
               'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
           }
       )
        
       # Handle preferred_job_types as a hidden field (will be managed by JavaScript)
       if 'preferred_job_types' in self.fields:
           self.fields['preferred_job_types'].widget = forms.HiddenInput()
           self.fields['preferred_job_types'].required = False
        
       # Set initial values for dynamic fields if instance exists
       if self.instance and self.instance.pk:
           # Skills are handled via JavaScript in template
           pass

    def clean(self):
        """Custom validation."""
        cleaned_data = super().clean()
        
        # If no currency is selected, set to USD as default
        if not cleaned_data.get('salary_currency'):
            cleaned_data['salary_currency'] = 'USD'
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ensure salary_currency has a default value
        if not instance.salary_currency:
            instance.salary_currency = 'USD'
        
        if commit:
            instance.save()
        return instance


class CompanyProfileForm(forms.ModelForm):
    """Form for editing company (recruiter) profile."""

    team_photos = forms.FileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
            'accept': 'image/*'
        }),
        help_text='Upload multiple team photos (JPG, PNG, GIF)'
    )

    verification_docs = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
            'accept': '.pdf,.doc,.docx,.jpg,.png'
        }),
        help_text='Upload business registration, tax documents, or other verification files'
    )

    class Meta:
        model = CompanyProfile
        fields = [
            'company_name',
            'logo',
            'industry',
            'company_size',
            'website',
            'description',
            'mission',
            'culture',
            'founded_year',
            'verification_status',
            'verification_docs'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Acme Inc.'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
                'accept': 'image/*'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Technology'
            }),
            'company_size': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'https://www.example.com'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Tell us about your company...',
                'rows': 4
            }),
            'mission': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'What is your company mission?',
                'rows': 3
            }),
            'culture': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Describe your company culture...',
                'rows': 3
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': '2020',
                'min': '1900',
                'max': '2026'
            }),
            'verification_status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
            }),
        }
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Acme Inc.'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
                'accept': 'image/*'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Technology'
            }),
            'company_size': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'https://www.example.com'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Tell us about your company...',
                'rows': 4
            }),
            'mission': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'What is your company mission?',
                'rows': 3
            }),
            'culture': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'Describe your company culture...',
                'rows': 3
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': '2020',
                'min': '1900',
                'max': '2026'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for dynamic fields if instance exists
        if self.instance and self.instance.pk:
            # Benefits and locations are handled via JavaScript in template
            pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for dynamic fields if instance exists
        if self.instance and self.instance.pk:
            # Benefits and locations are handled via JavaScript in template
            pass


class SkillForm(forms.Form):
    """Form for adding/editing a single skill."""
    
    skill = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'e.g., React, Python, AWS'
        })
    )
    
    proficiency = forms.ChoiceField(
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition'
        })
    )


class ExperienceForm(forms.Form):
    """Form for adding/editing work experience."""
    
    company = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'Acme Inc.'
        })
    )
    
    role = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'Senior Developer'
        })
    )
    
    start_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'type': 'month'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'type': 'month'
        })
    )
    
    current = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'Describe your responsibilities and achievements...',
            'rows': 3
        })
    )


class EducationForm(forms.Form):
    """Form for adding/editing education."""
    
    institution = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'Stanford University'
        })
    )
    
    degree = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'Bachelor of Science'
        })
    )
    
    field = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'Computer Science'
        })
    )
    
    start_year = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '2015',
            'min': '1950',
            'max': '2026'
        })
    )
    
    end_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '2019',
            'min': '1950',
            'max': '2030'
        })
    )


class EmailPreferencesForm(forms.ModelForm):
    """Form for managing email notification preferences."""
    
    class Meta:
        model = EmailPreferences
        fields = [
            'email_frequency',
            'notify_new_application',
            'notify_application_status_changed',
            'notify_new_message',
            'notify_profile_viewed',
            'notify_new_follower',
            'notify_followed_company_job',
            'notify_interview_scheduled',
            'notify_job_recommendations',
            'notify_new_applicant',
            'notify_screening_complete',
            'notify_job_expiring_soon',
            'notify_applicant_response',
            'notify_new_company_follower',
        ]
        widgets = {
            'email_frequency': forms.RadioSelect(attrs={
                'class': 'focus:ring-blue',
                'data-toggle': 'frequency-toggle'
            }),
            'notify_new_application': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'new_application'
            }),
            'notify_application_status_changed': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'application_status_changed'
            }),
            'notify_new_message': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'new_message'
            }),
            'notify_profile_viewed': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'profile_viewed'
            }),
            'notify_new_follower': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'new_follower'
            }),
            'notify_followed_company_job': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'followed_company_job'
            }),
            'notify_interview_scheduled': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'interview_scheduled'
            }),
            'notify_job_recommendations': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'job_recommendations'
            }),
            'notify_new_applicant': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'new_applicant'
            }),
            'notify_screening_complete': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'screening_complete'
            }),
            'notify_job_expiring_soon': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'job_expiring_soon'
            }),
            'notify_applicant_response': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'applicant_response'
            }),
            'notify_new_company_follower': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue border-gray-300 rounded focus:ring-blue',
                'data-notification': 'new_company_follower'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_frequency'].widget.attrs.update({
            'class': 'focus:ring-blue'
        })
        
        # Get user to determine which notification fields to show
        if self.instance and self.instance.user:
            user = self.instance.user
            
            # Hide company-only fields for personal accounts
            if user.account_type == 'personal':
                company_fields = [
                    'notify_new_applicant',
                    'notify_screening_complete',
                    'notify_job_expiring_soon',
                    'notify_applicant_response',
                    'notify_new_company_follower',
                ]
                for field_name in company_fields:
                    del self.fields[field_name]
            
            # Hide personal-only fields for company accounts
            elif user.account_type == 'company':
                personal_fields = [
                    'notify_new_application',
                    'notify_application_status_changed',
                    'notify_profile_viewed',
                    'notify_new_follower',
                    'notify_followed_company_job',
                    'notify_interview_scheduled',
                    'notify_job_recommendations',
                ]
                for field_name in personal_fields:
                    del self.fields[field_name]


class ChangeEmailForm(forms.Form):
    """Form for requesting email change with verification."""
    
    new_email = forms.EmailField(
        label='New Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your new email address'
        })
    )
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your current password'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_new_email(self):
        """Validate new email."""
        new_email = self.cleaned_data.get('new_email')
        
        # Check if email is already in use
        if User.objects.filter(email__iexact=new_email).exists():
            raise forms.ValidationError('This email address is already in use.')
        
        # Check if it's the same as current email
        if new_email.lower() == self.user.email.lower():
            raise forms.ValidationError('This is already your current email address.')
        
        return new_email
    
    def clean_current_password(self):
        """Validate current password."""
        current_password = self.cleaned_data.get('current_password')
        
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Incorrect password.')
        
        return current_password
    
    
class CustomPasswordChangeForm(PasswordChangeForm):
    """Form for changing password while logged in."""
    
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )
    
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )
    
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        })
    )


class DeleteAccountForm(forms.Form):
    """Form for confirming account deletion."""
    
    password = forms.CharField(
        label='Confirm Your Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition',
            'placeholder': 'Enter your password to confirm',
            'autocomplete': 'current-password'
        })
    )
    
    confirm_text = forms.CharField(
        label='Type "DELETE" to confirm',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition',
            'placeholder': 'DELETE',
            'autocomplete': 'off'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """Validate password."""
        password = self.cleaned_data.get('password')
        
        if not self.user.check_password(password):
            raise forms.ValidationError('Incorrect password.')
        
        return password
    
    def clean_confirm_text(self):
        """Validate confirmation text."""
        confirm_text = self.cleaned_data.get('confirm_text')
        
        if confirm_text != 'DELETE':
            raise forms.ValidationError('You must type "DELETE" to confirm.')
        
        return confirm_text


class Enable2FAForm(forms.Form):
    """Form for enabling two-factor authentication."""
    
    token = forms.CharField(
        label='Verification Code',
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl text-center font-mono tracking-wider focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '000000',
            'maxlength': '6',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}'
        })
    )
    
    def clean_token(self):
        """Validate token format."""
        token = self.cleaned_data.get('token')
        
        if not token.isdigit():
            raise forms.ValidationError('Token must contain only numbers.')
        
        return token


class Verify2FAForm(forms.Form):
    """Form for verifying 2FA token during login."""
    
    token = forms.CharField(
        label='Authentication Code',
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl text-center font-mono tracking-wider focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': '000000',
            'maxlength': '6',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'autofocus': True
        })
    )
    
    def clean_token(self):
        """Validate token format."""
        token = self.cleaned_data.get('token')
        
        if not token.isdigit():
            raise forms.ValidationError('Token must contain only numbers.')
        
        return token


class ResumeImportForm(forms.Form):
    """Form for importing resume data into user profile."""
    
    resume_file = forms.FileField(
        label='Resume File',
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition file:mr-4 file:py-2 file:px-4 file:rounded-l-xl file:border-0 file:text-sm file:font-semibold file:bg-blue file:text-white hover:file:bg-blue-600',
            'accept': '.pdf,.docx,.txt'
        }),
        help_text='Upload your resume in PDF, DOCX, or TXT format. We\'ll extract your information and suggest updates to your profile.'
    )
    
    import_options = forms.MultipleChoiceField(
        choices=[
            ('personal_info', 'Personal Information (name, contact details)'),
            ('education', 'Education History'),
            ('experience', 'Work Experience'),
            ('skills', 'Skills and Technologies'),
            ('certifications', 'Certifications and Licenses'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        }),
        initial=['personal_info', 'education', 'experience', 'skills', 'certifications'],
        help_text='Select which information you want to import from your resume.'
    )
    
    merge_strategy = forms.ChoiceField(
        choices=[
            ('replace', 'Replace existing data'),
            ('merge', 'Merge with existing data (recommended)'),
            ('preview', 'Preview changes only (no changes saved)'),
        ],
        required=True,
        initial='merge',
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-2'
        }),
        help_text='Choose how to handle conflicts with existing profile data.'
    )
    
    def clean_resume_file(self):
        """Validate the uploaded resume file."""
        resume_file = self.cleaned_data.get('resume_file')
        
        if not resume_file:
            return resume_file
            
        # Check file size (max 10MB)
        if resume_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 10MB.')
        
        # Check file extension
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_name = resume_file.name.lower()
        
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise forms.ValidationError('Only PDF, DOCX, and TXT files are allowed.')
        
        # Check MIME type
        allowed_mime_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        
        if hasattr(resume_file, 'content_type') and resume_file.content_type not in allowed_mime_types:
            raise forms.ValidationError('Invalid file type. Please upload a valid resume file.')
        
        return resume_file


class CreateAPIKeyForm(forms.Form):
    """Form for creating a new API key."""
    
    name = forms.CharField(
        label='Key Name',
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
            'placeholder': 'e.g., Production API, Mobile App',
            'autocomplete': 'off'
        }),
        help_text='Give this API key a descriptive name so you can identify it later.'
    )
    
    def clean_name(self):
        """Validate and clean the key name."""
        name = self.cleaned_data.get('name').strip()
        
        if len(name) < 3:
            raise forms.ValidationError('Key name must be at least 3 characters long.')
        
        return name