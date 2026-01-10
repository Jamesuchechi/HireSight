from django import forms
from django.core.exceptions import ValidationError
from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    """Form for uploading a new resume."""

    class Meta:
        model = Resume
        fields = ['title', 'file', 'is_primary']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'e.g., Software Engineer Resume'
            }),
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-xl cursor-pointer focus:outline-none',
                'accept': '.pdf,.docx'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue focus:ring-blue'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError('Please select a file to upload.')

        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if file.size > max_size:
            raise ValidationError('File size must be less than 5MB.')

        # Check file extension
        allowed_extensions = ['.pdf', '.docx']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise ValidationError('Only PDF and DOCX files are allowed.')

        return file

    def save(self, commit=True):
        """Save the resume with user."""
        instance = super().save(commit=False)
        instance.user = self.user
        instance.original_filename = self.cleaned_data['file'].name

        if commit:
            instance.save()
        return instance


class ResumeEditForm(forms.ModelForm):
    """Form for editing resume metadata."""

    class Meta:
        model = Resume
        fields = ['title', 'is_primary']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue focus:border-blue transition',
                'placeholder': 'e.g., Software Engineer Resume'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue focus:ring-blue'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

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