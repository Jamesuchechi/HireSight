"""
Forms for screening system.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .models import ScreeningSession, ScreeningCriteria, ScreeningResult
from apps.jobs.models import Job


class ScreeningSessionForm(forms.ModelForm):
    """Form for creating a screening session."""
    
    class Meta:
        model = ScreeningSession
        fields = ['title', 'job']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
                'placeholder': 'e.g., Data Analyst Q1 2024 Screening'
            }),
            'job': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter jobs to only show company's jobs
        if self.company:
            self.fields['job'].queryset = Job.objects.filter(
                company=self.company,
                status='active'
            ).order_by('-created_at')
        
        # Make job optional
        self.fields['job'].required = False
        self.fields['job'].empty_label = "General Screening (No specific job)"
    
    def clean_title(self):
        """Validate title."""
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) == 0:
            raise ValidationError("Session title is required.")
        if len(title) < 3:
            raise ValidationError("Session title must be at least 3 characters.")
        return title.strip()


class ScreeningCriteriaForm(forms.ModelForm):
    """Form for setting up screening criteria."""
    
    # Skills fields with better input
    required_skills_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
            'rows': 3,
            'placeholder': 'Enter required skills separated by commas (e.g., Python, Django, SQL)'
        }),
        label='Required Skills',
        help_text='Enter skills separated by commas'
    )
    
    nice_to_have_skills_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
            'rows': 3,
            'placeholder': 'Enter nice-to-have skills separated by commas'
        }),
        label='Nice-to-Have Skills',
        help_text='Enter skills separated by commas'
    )
    
    class Meta:
        model = ScreeningCriteria
        fields = [
            'min_experience_years',
            'max_experience_years',
            'weight_skills',
            'weight_experience',
            'weight_education',
            'weight_keywords'
        ]
        widgets = {
            'min_experience_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
                'min': 0,
                'step': 0.5,
                'placeholder': '0'
            }),
            'max_experience_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
                'min': 0,
                'step': 0.5,
                'placeholder': 'Optional'
            }),
            'weight_skills': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
                'min': 0,
                'max': 100,
                'step': 0.1,
                'value': 40
            }),
            'weight_experience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
                'min': 0,
                'max': 100,
                'step': 0.1,
                'value': 30
            }),
            'weight_education': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
                'min': 0,
                'max': 100,
                'step': 0.1,
                'value': 20
            }),
            'weight_keywords': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary',
                'min': 0,
                'max': 100,
                'step': 0.1,
                'value': 10
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        # Set default weights (as percentages)
        if not self.instance.pk:
            self.fields['weight_skills'].initial = 40
            self.fields['weight_experience'].initial = 30
            self.fields['weight_education'].initial = 20
            self.fields['weight_keywords'].initial = 10
        else:
            # Convert stored decimal values to percentages for display
            if self.instance.weight_skills:
                self.fields['weight_skills'].initial = self.instance.weight_skills * 100
            if self.instance.weight_experience:
                self.fields['weight_experience'].initial = self.instance.weight_experience * 100
            if self.instance.weight_education:
                self.fields['weight_education'].initial = self.instance.weight_education * 100
            if self.instance.weight_keywords:
                self.fields['weight_keywords'].initial = self.instance.weight_keywords * 100
        
        # Pre-fill skills if instance exists
        if self.instance.pk:
            if self.instance.required_skills:
                self.fields['required_skills_input'].initial = ', '.join(self.instance.required_skills)
            if self.instance.nice_to_have_skills:
                self.fields['nice_to_have_skills_input'].initial = ', '.join(self.instance.nice_to_have_skills)
    
    def clean_required_skills_input(self):
        """Convert comma-separated string to list."""
        skills_str = self.cleaned_data.get('required_skills_input', '')
        if skills_str:
            skills = [s.strip() for s in skills_str.split(',') if s.strip()]
            return skills
        return []
    
    def clean_nice_to_have_skills_input(self):
        """Convert comma-separated string to list."""
        skills_str = self.cleaned_data.get('nice_to_have_skills_input', '')
        if skills_str:
            skills = [s.strip() for s in skills_str.split(',') if s.strip()]
            return skills
        return []
    
    def clean(self):
        """Validate weights sum to 1."""
        cleaned_data = super().clean()
        
        # Get weights (they come as percentages from the form, convert to decimals)
        weight_skills = cleaned_data.get('weight_skills', 0)
        weight_experience = cleaned_data.get('weight_experience', 0)
        weight_education = cleaned_data.get('weight_education', 0)
        weight_keywords = cleaned_data.get('weight_keywords', 0)
        
        # Convert percentages to decimals if they're > 1 (user entered 0-100 range)
        if weight_skills and weight_skills > 1:
            weight_skills = weight_skills / 100
            cleaned_data['weight_skills'] = weight_skills
        
        if weight_experience and weight_experience > 1:
            weight_experience = weight_experience / 100
            cleaned_data['weight_experience'] = weight_experience
        
        if weight_education and weight_education > 1:
            weight_education = weight_education / 100
            cleaned_data['weight_education'] = weight_education
        
        if weight_keywords and weight_keywords > 1:
            weight_keywords = weight_keywords / 100
            cleaned_data['weight_keywords'] = weight_keywords
        
        # Validate weights sum to approximately 1.0
        total_weight = weight_skills + weight_experience + weight_education + weight_keywords
        if not (0.99 <= total_weight <= 1.01):
            raise ValidationError(
                f"Weights must sum to 100%. Current sum: {(total_weight * 100):.1f}%"
            )
        
        # Validate experience range
        min_exp = cleaned_data.get('min_experience_years')
        max_exp = cleaned_data.get('max_experience_years')
        if min_exp and max_exp and max_exp < min_exp:
            raise ValidationError(
                "Maximum experience cannot be less than minimum experience."
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save criteria with skills as lists."""
        criteria = super().save(commit=False)
        
        # Set skills from input fields
        criteria.required_skills = self.cleaned_data.get('required_skills_input', [])
        criteria.nice_to_have_skills = self.cleaned_data.get('nice_to_have_skills_input', [])
        
        # Set session if provided
        if self.session and not criteria.session_id:
            criteria.session = self.session
        
        if commit:
            criteria.save()
        
        return criteria


class BulkResumeUploadForm(forms.Form):
    """Form for bulk resume upload."""
    
    resumes = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-input w-full',
            'accept': '.pdf,.doc,.docx'
        }),
        label='Upload Resumes',
        help_text='Select multiple resume files (PDF, DOC, DOCX). Maximum 50 files.',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        self.max_files = kwargs.pop('max_files', 50)
        super().__init__(*args, **kwargs)
    
    def clean_resumes(self):
        """Validate uploaded resumes."""
        files = self.files.getlist('resumes')
        
        if not files:
            raise ValidationError("Please select at least one resume file.")
        
        if len(files) > self.max_files:
            raise ValidationError(f"Maximum {self.max_files} files allowed. You uploaded {len(files)}.")
        
        # Validate file sizes (max 5MB per file)
        max_size = 5 * 1024 * 1024  # 5MB
        for file in files:
            if file.size > max_size:
                raise ValidationError(
                    f"File {file.name} is too large ({file.size / 1024 / 1024:.1f}MB). "
                    f"Maximum size is 5MB."
                )
        
        return files


class ScreeningResultFilterForm(forms.Form):
    """Form for filtering screening results."""
    
    SCORE_RANGES = [
        ('', 'All Scores'),
        ('90-100', '90-100% (Excellent)'),
        ('80-89', '80-89% (Strong)'),
        ('70-79', '70-79% (Good)'),
        ('60-69', '60-69% (Fair)'),
        ('0-59', '0-59% (Weak)'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]
    
    score_range = forms.ChoiceField(
        choices=SCORE_RANGES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select rounded-md border-gray-300'})
    )
    
    min_score = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'Min'
        })
    )
    
    max_score = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'Max'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
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
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-match_score', 'Match Score (High to Low)'),
            ('match_score', 'Match Score (Low to High)'),
            ('-processed_at', 'Recently Processed'),
            ('processed_at', 'Oldest First'),
        ],
        required=False,
        initial='-match_score',
        widget=forms.Select(attrs={'class': 'form-select rounded-md border-gray-300'})
    )
    
    def clean(self):
        """Validate filter form."""
        cleaned_data = super().clean()
        
        # Validate score range
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        if min_score is not None and max_score is not None and min_score > max_score:
            raise ValidationError("Minimum score cannot be greater than maximum score.")
        
        # Parse score range if provided
        score_range = cleaned_data.get('score_range')
        if score_range:
            try:
                min_val, max_val = score_range.split('-')
                cleaned_data['score_range_min'] = int(min_val)
                cleaned_data['score_range_max'] = int(max_val)
            except ValueError:
                pass
        
        return cleaned_data


class ScreeningResultExportForm(forms.Form):
    """Form for exporting screening results."""
    
    FORMAT_CHOICES = [
        ('csv', 'CSV (Comma Separated Values)'),
        ('excel', 'Excel Spreadsheet'),
        ('pdf', 'PDF Report'),
    ]
    
    export_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        required=True,
        initial='excel',
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    include_fields = forms.MultipleChoiceField(
        choices=[
            ('personal_info', 'Personal Information'),
            ('contact', 'Contact Details'),
            ('skills', 'Skills'),
            ('experience', 'Experience'),
            ('education', 'Education'),
            ('match_details', 'Match Analysis'),
            ('notes', 'Notes'),
        ],
        required=True,
        initial=['personal_info', 'skills', 'match_details'],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'})
    )
    
    only_shortlisted = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-blue-600'})
    )
    
    min_score = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-md border-gray-300',
            'placeholder': 'e.g., 70'
        }),
        label='Minimum Match Score'
    )
    
    include_resume_links = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-blue-600'}),
        label='Include Resume Download Links'
    )


class ScreeningSessionUpdateForm(forms.ModelForm):
    """Form for updating screening session details."""
    
    class Meta:
        model = ScreeningSession
        fields = ['title', 'settings']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'settings': forms.Textarea(attrs={
                'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'rows': 4
            }),
        }


class ScreeningResultNoteForm(forms.Form):
    """Form for adding notes to screening results."""
    
    note = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Add a note about this candidate...'
        }),
        label='Note'
    )
    
    is_important = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-blue-600'}),
        label='Mark as Important'
    )


class PushToPipelineForm(forms.Form):
    """Form for pushing candidates to pipeline."""
    
    result_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    job = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-select w-full rounded-md border-gray-300'
        }),
        label='Target Job Position',
        help_text='Select the job to push candidates to'
    )
    
    include_notes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-blue-600'}),
        label='Include Screening Notes'
    )
    
    notification_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea w-full rounded-md border-gray-300',
            'rows': 3,
            'placeholder': 'Optional message to include with pipeline push...'
        }),
        label='Notification Message'
    )
    
    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            # Filter jobs to company's active jobs
            self.fields['job'].queryset = company.jobs.filter(status='active')


class BulkPushToPipelineForm(forms.Form):
    """Form for bulk pushing candidates to pipeline."""
    
    result_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    jobs = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        }),
        label='Target Job Positions',
        help_text='Select one or more jobs to push candidates to'
    )
    
    strategy = forms.ChoiceField(
        choices=[
            ('best_match', 'Best Match Job (auto-select)'),
            ('all', 'All Selected Jobs'),
            ('filtered', 'Only matching jobs (min 70%)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
        initial='best_match',
        label='Push Strategy'
    )
    
    notify_recruiters = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox rounded text-blue-600'}),
        label='Notify Recruiters'
    )
    
    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['jobs'].queryset = company.jobs.filter(status='active')
