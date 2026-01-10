from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from .models import User, PersonalProfile, CompanyProfile


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
        }


class CompanyProfileForm(forms.ModelForm):
    """Form for editing company (recruiter) profile."""
    
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
            'founded_year'
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
        }


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