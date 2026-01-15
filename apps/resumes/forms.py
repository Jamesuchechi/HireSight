import os
import magic
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    """Form for uploading a new resume."""

    class Meta:
        model = Resume
        fields = ['title', 'file', 'is_primary']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition',
                'placeholder': 'e.g., Software Engineer Resume'
            }),
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
                'accept': '.pdf,.docx,.txt'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary focus:ring-primary'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make file field required
        self.fields['file'].required = True

    def clean_title(self):
        """Validate title is unique for user."""
        title = self.cleaned_data.get('title')
        
        if not title:
            raise ValidationError('Resume title is required.')
        
        # Check for duplicate titles for this user
        if self.user:
            existing = Resume.objects.filter(
                user=self.user,
                title__iexact=title
            )
            
            # Exclude current instance when editing
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    'You already have a resume with this title. '
                    'Please choose a different title.'
                )
        
        return title.strip()

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError('Please select a file to upload.')

        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if file.size > max_size:
            raise ValidationError(
                f'File size must be less than 5MB. '
                f'Your file is {file.size / (1024 * 1024):.2f}MB.'
            )

        # Check file extension
        allowed_extensions = ['pdf', 'docx', 'txt']
        file_extension = file.name.lower().split('.')[-1]
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f'Only PDF, DOCX, and TXT files are allowed. '
                f'You uploaded a .{file_extension} file.'
            )

        # Validate MIME type for extra security
        try:
            # Read first 2048 bytes to determine file type
            file.seek(0)
            file_start = file.read(2048)
            file.seek(0)  # Reset file pointer
            
            mime = magic.from_buffer(file_start, mime=True)
            
            valid_mimes = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain'
            ]
            
            if mime not in valid_mimes:
                raise ValidationError(
                    f'Invalid file type. The file appears to be {mime}, '
                    f'but only PDF, DOCX, and TXT files are allowed.'
                )
        except Exception:
            # If python-magic is not installed, skip MIME validation
            pass

        # Basic content validation - check file is not empty
        if file.size < 100:  # Less than 100 bytes is suspicious
            raise ValidationError(
                'The uploaded file appears to be empty or corrupted.'
            )

        return file

    def save(self, commit=True):
        """Save the resume with user."""
        instance = super().save(commit=False)
        instance.user = self.user
        
        # Store original filename
        if self.cleaned_data.get('file'):
            instance.original_filename = self.cleaned_data['file'].name

        if commit:
            instance.save()
        return instance


class ResumeEditForm(forms.ModelForm):
    """Form for editing resume metadata (without file upload)."""

    class Meta:
        model = Resume
        fields = ['title', 'is_primary']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition',
                'placeholder': 'e.g., Software Engineer Resume'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary focus:ring-primary'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_title(self):
        """Validate title is unique for user."""
        title = self.cleaned_data.get('title')
        
        if not title:
            raise ValidationError('Resume title is required.')
        
        # Check for duplicate titles for this user
        if self.user:
            existing = Resume.objects.filter(
                user=self.user,
                title__iexact=title
            ).exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    'You already have a resume with this title. '
                    'Please choose a different title.'
                )
        
        return title.strip()

    def save(self, commit=True):
        """Save with primary resume logic."""
        instance = super().save(commit=False)

        if instance.is_primary:
            # Ensure only one primary resume per user
            Resume.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(pk=instance.pk).update(is_primary=False)

        if commit:
            instance.save()
        return instance


class ResumeReplaceFileForm(forms.ModelForm):
    """Form for replacing the file of an existing resume."""

    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
                'accept': '.pdf,.docx,.txt'
            }),
        }

    def clean_file(self):
        """Validate uploaded file (same as ResumeUploadForm)."""
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError('Please select a file to upload.')

        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if file.size > max_size:
            raise ValidationError(
                f'File size must be less than 5MB. '
                f'Your file is {file.size / (1024 * 1024):.2f}MB.'
            )

        # Check file extension
        allowed_extensions = ['pdf', 'docx', 'txt']
        file_extension = file.name.lower().split('.')[-1]
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f'Only PDF, DOCX, and TXT files are allowed. '
                f'You uploaded a .{file_extension} file.'
            )

        return file

    def save(self, commit=True):
        """Save and reset parsing status."""
        instance = super().save(commit=False)
        
        # Reset parsing status when file is replaced
        instance.status = 'uploaded'
        instance.parsed_text = ''
        instance.skills = []
        instance.experience_years = None
        instance.education = []
        instance.contact_info = {}
        instance.parsed_at = None
        instance.error_message = ''
        instance.parse_attempts = 0
        instance.last_parse_attempt = None
        
        # Update original filename
        if self.cleaned_data.get('file'):
            instance.original_filename = self.cleaned_data['file'].name

        if commit:
            instance.save()
        return instance


class BulkResumeDeleteForm(forms.Form):
    """Form for bulk deleting resumes."""
    
    resume_ids = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_resume_ids(self):
        """Validate resume IDs belong to user."""
        ids_str = self.cleaned_data.get('resume_ids', '')
        
        try:
            ids = [int(id) for id in ids_str.split(',') if id]
        except ValueError:
            raise ValidationError('Invalid resume IDs.')
        
        if not ids:
            raise ValidationError('No resumes selected.')
        
        # Verify all IDs belong to user
        if self.user:
            user_resume_ids = Resume.objects.filter(
                user=self.user,
                pk__in=ids
            ).values_list('pk', flat=True)
            
            if len(user_resume_ids) != len(ids):
                raise ValidationError('Some resumes do not belong to you.')
        
        return ids