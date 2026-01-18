from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Job, SavedJob, JobStatus, RemoteType, EmploymentType, ExperienceLevel
import json


class QuillEditorWidget(forms.Textarea):
    """Custom widget for Quill rich text editor."""

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'quill-editor',
            'style': 'display: none;'  # Hidden textarea, Quill will show the editor
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # Add data attributes for Quill configuration
        attrs['data-quill-placeholder'] = 'Describe the role, responsibilities, and what the candidate will be doing...'
        return attrs

class JobCreateForm(forms.ModelForm):
    """Form for creating a new job posting."""
    
    # Override JSONFields with TextFields for easier user input
    requirements_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-vertical',
            'rows': 6,
            'placeholder': 'List the required skills, experience, and qualifications (one per line or comma-separated)'
        }),
        label='Requirements',
        help_text='Enter each requirement on a new line or separate with commas'
    )
    
    tags_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
            'placeholder': 'Python, Django, React, JavaScript'
        }),
        label='Skills & Tags',
        help_text='Enter skills separated by commas'
    )

    class Meta:
        model = Job
        fields = [
            'title', 'description', 'responsibilities',
            'nice_to_have', 'benefits', 'location', 'is_remote', 'remote_type',
            'employment_type', 'experience_level', 'salary_min', 'salary_max',
            'salary_period', 'positions_available', 'application_deadline',
            'requires_cover_letter', 'requires_portfolio', 'application_email',
            'status', 'department', 'education_required'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'placeholder': 'e.g., Senior Software Engineer'
            }),
            'description': QuillEditorWidget(attrs={
                'class': 'quill-editor',
                'rows': 8,
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-vertical',
                'rows': 6,
                'placeholder': 'List key responsibilities (one per line or comma-separated)'
            }),
            'nice_to_have': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-vertical',
                'rows': 4,
                'placeholder': 'Nice-to-have skills and qualifications'
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-vertical',
                'rows': 4,
                'placeholder': 'Health insurance, 401k, flexible hours, etc.'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'placeholder': 'e.g., San Francisco, CA or Remote'
            }),
            'remote_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            }),
            'employment_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            }),
            'salary_min': forms.NumberInput(attrs={
                'class': 'px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'placeholder': 'Min'
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'placeholder': 'Max'
            }),
            'salary_period': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            }),
            'positions_available': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'min': 1
            }),
            'application_deadline': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'type': 'date'
            }),
            'application_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'placeholder': 'hiring@company.com'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            }),
            'department': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'placeholder': 'e.g., Engineering, Marketing'
            }),
            'education_required': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
                'placeholder': "e.g., Bachelor's degree in Computer Science"
            }),
    }

    screening_questions = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    is_remote = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'
        })
    )
    requires_cover_letter = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'
        })
    )
    requires_portfolio = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'
        })
    )

    def __init__(self, *args, company=None, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)

        # Make certain fields optional
        self.fields['responsibilities'].required = False
        self.fields['nice_to_have'].required = False
        self.fields['benefits'].required = False
        self.fields['salary_min'].required = False
        self.fields['salary_max'].required = False
        self.fields['application_deadline'].required = False
        self.fields['application_email'].required = False
        self.fields['department'].required = False
        self.fields['education_required'].required = False
        
        # If editing existing job, populate text fields from JSON
        if self.instance and self.instance.pk:
            # Convert requirements JSON to text
            if self.instance.requirements:
                if isinstance(self.instance.requirements, dict):
                    skills = self.instance.requirements.get('skills', [])
                    if skills:
                        self.initial['requirements_text'] = '\n'.join(skills)
                    else:
                        # If there are other keys, just show them as text
                        self.initial['requirements_text'] = str(self.instance.requirements)
            
            # Convert tags JSON to text
            if self.instance.tags:
                if isinstance(self.instance.tags, list):
                    self.initial['tags_text'] = ', '.join(self.instance.tags)
            if self.instance.screening_questions:
                try:
                    self.initial['screening_questions'] = json.dumps(self.instance.screening_questions)
                except (TypeError, ValueError):
                    self.initial['screening_questions'] = '[]'

    def clean_title(self):
        """Validate job title."""
        title = self.cleaned_data.get('title')
        
        if not title:
            raise ValidationError('Job title is required.')
        
        if len(title) < 5:
            raise ValidationError('Job title must be at least 5 characters long.')
        
        return title.strip()

    def clean_salary_max(self):
        """Validate salary max is greater than min."""
        salary_min = self.cleaned_data.get('salary_min')
        salary_max = self.cleaned_data.get('salary_max')
        
        if salary_min and salary_max:
            if salary_max < salary_min:
                raise ValidationError('Maximum salary must be greater than minimum salary.')
        
        return salary_max

    def clean_application_deadline(self):
        """Validate application deadline is in the future."""
        deadline = self.cleaned_data.get('application_deadline')
        
        if deadline:
            if deadline < timezone.now():
                raise ValidationError('Application deadline must be in the future.')
        
        return deadline

    def clean_description(self):
        """Validate description length."""
        description = self.cleaned_data.get('description')
        
        if not description:
            raise ValidationError('Job description is required.')
        
        if len(description) < 100:
            raise ValidationError('Job description must be at least 100 characters long.')
        
        return description

    def clean_requirements_text(self):
        """Convert requirements text to JSON format."""
        requirements_text = self.cleaned_data.get('requirements_text', '').strip()
        
        if not requirements_text:
            return {}
        
        # Try to parse as JSON first (in case user enters JSON)
        try:
            parsed = json.loads(requirements_text)
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list):
                return {'skills': parsed}
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Parse as plain text - split by newlines or commas
        requirements = []
        
        # Split by newlines first
        lines = requirements_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # If line contains commas, split further
            if ',' in line:
                items = [item.strip() for item in line.split(',') if item.strip()]
                requirements.extend(items)
            else:
                requirements.append(line)
        
        return {'skills': requirements} if requirements else {}

    def clean_tags_text(self):
        """Convert tags text to JSON list format."""
        tags_text = self.cleaned_data.get('tags_text', '').strip()
        
        if not tags_text:
            return []
        
        # Try to parse as JSON first
        try:
            parsed = json.loads(tags_text)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, str):
                # If it's a JSON string, split it
                return [parsed]
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Parse as comma-separated values
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        return tags

    def clean_screening_questions(self):
        """Parse screening questions JSON from the hidden textarea."""
        data = self.cleaned_data.get('screening_questions', '').strip()

        if not data:
            return []

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            raise ValidationError('Invalid screening questions data.')

        if not isinstance(parsed, list):
            raise ValidationError('Screening questions must be submitted as a list.')

        return parsed

    def save(self, commit=True):
        """Save job with company and converted JSON fields."""
        instance = super().save(commit=False)
        
        # Set company
        if self.company:
            instance.company = self.company
        
        # Convert text fields to JSON
        instance.requirements = self.cleaned_data.get('requirements_text') or {}
        instance.tags = self.cleaned_data.get('tags_text') or []
        instance.screening_questions = self.cleaned_data.get('screening_questions') or []
        
        if commit:
            instance.save()
        
        return instance


class JobEditForm(JobCreateForm):
    """Form for editing existing job posting."""
    
    class Meta(JobCreateForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Can't change company after creation
        if 'company' in self.fields:
            del self.fields['company']


class JobFilterForm(forms.Form):
    """Form for filtering and searching jobs."""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition',
            'placeholder': 'Job title, company, or keywords'
        })
    )

    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition',
            'placeholder': 'City, State'
        })
    )

    location_radius = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any Distance'),
            ('5', 'Within 5 miles'),
            ('10', 'Within 10 miles'),
            ('25', 'Within 25 miles'),
            ('50', 'Within 50 miles'),
            ('100', 'Within 100 miles'),
        ],
        initial='25',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition'
        })
    )

    remote_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(RemoteType.choices),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition'
        })
    )

    employment_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(EmploymentType.choices),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition'
        })
    )

    experience_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Experience')] + list(ExperienceLevel.choices),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition'
        })
    )

    salary_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition',
            'placeholder': '50000'
        })
    )

    posted_within = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any Time'),
            ('1', 'Last 24 hours'),
            ('3', 'Last 3 days'),
            ('7', 'Last week'),
            ('30', 'Last month'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition'
        })
    )

    skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition',
            'placeholder': 'Python, Django, React, etc.'
        })
    )

    skills_match = forms.ChoiceField(
        required=False,
        choices=[
            ('any', 'Match ANY skill (OR)'),
            ('all', 'Match ALL skills (AND)'),
        ],
        initial='any',
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-2'
        })
    )

    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('relevance', 'Most Relevant'),
            ('recommendations', 'Recommended for You'),
            ('date', 'Most Recent'),
            ('salary', 'Highest Salary'),
        ],
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition text-sm'
        })
    )


class JobQuickEditForm(forms.ModelForm):
    """Quick edit form for status changes."""

    class Meta:
        model = Job
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            })
        }


class JobDuplicateForm(forms.Form):
    """Form for duplicating a job with modifications."""

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
            'placeholder': 'New job title'
        })
    )

    status = forms.ChoiceField(
        choices=JobStatus.choices,
        initial=JobStatus.DRAFT,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
        })
    )

    def clean_title(self):
        """Validate title."""
        title = self.cleaned_data.get('title')
        
        if not title:
            raise ValidationError('Job title is required.')
        
        if len(title) < 5:
            raise ValidationError('Job title must be at least 5 characters long.')
        
        return title.strip()


class SavedJobForm(forms.ModelForm):
    """Form for saving/bookmarking jobs."""

    class Meta:
        model = SavedJob
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-vertical',
                'rows': 3,
                'placeholder': 'Add personal notes about this job (optional)'
            })
        }

    def __init__(self, *args, user=None, job=None, **kwargs):
        self.user = user
        self.job = job
        super().__init__(*args, **kwargs)
        
        self.fields['notes'].required = False

    def save(self, commit=True):
        """Save with user and job."""
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        if self.job:
            instance.job = self.job
        
        if commit:
            instance.save()
        
        return instance


class JobEditForm(JobCreateForm):
    """Form for editing existing job posting."""
    
    class Meta(JobCreateForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Can't change company after creation
        if 'company' in self.fields:
            del self.fields['company']


class SavedJobForm(forms.ModelForm):
    """Form for saving/bookmarking jobs."""

    class Meta:
        model = SavedJob
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-vertical',
                'rows': 3,
                'placeholder': 'Add personal notes about this job (optional)'
            })
        }

    def __init__(self, *args, user=None, job=None, **kwargs):
        self.user = user
        self.job = job
        super().__init__(*args, **kwargs)
        
        self.fields['notes'].required = False

    def save(self, commit=True):
        """Save with user and job."""
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        if self.job:
            instance.job = self.job
        
        if commit:
            instance.save()
        
        return instance
