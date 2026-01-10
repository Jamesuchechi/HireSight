import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Resume
from .forms import ResumeUploadForm, ResumeEditForm
from .parsers import resume_parser


class ResumeListView(LoginRequiredMixin, ListView):
    """List all resumes for the current user."""
    model = Resume
    template_name = 'resumes/resume_list.html'
    context_object_name = 'resumes'

    def get_queryset(self):
        """Return resumes for current user."""
        return Resume.objects.filter(user=self.request.user)


class ResumeUploadView(LoginRequiredMixin, CreateView):
    """Upload a new resume."""
    model = Resume
    form_class = ResumeUploadForm
    template_name = 'resumes/resume_upload.html'
    success_url = reverse_lazy('resumes:list')

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle successful form submission."""
        resume = form.save()

        # Start parsing in background (for now, do it synchronously)
        try:
            # Parse the resume
            result = resume_parser.parse_file(
                resume.file.path,
                resume.original_filename
            )

            if result['success']:
                resume.parsed_text = result['text']
                resume.skills = result.get('skills', [])
                resume.experience_years = result.get('experience_years')
                resume.education = result.get('education', [])
                resume.contact_info = result.get('contact_info', {})
                resume.status = 'parsed'
                resume.parsed_at = timezone.now()
            else:
                resume.status = 'failed'
                resume.error_message = result.get('error', 'Unknown parsing error')

            resume.save()

            if result['success']:
                messages.success(self.request, 'Resume uploaded and parsed successfully!')
            else:
                messages.warning(self.request, f'Resume uploaded but parsing failed: {resume.error_message}')

        except Exception as e:
            resume.status = 'failed'
            resume.error_message = str(e)
            resume.save()
            messages.warning(self.request, f'Resume uploaded but parsing failed: {str(e)}')

        return super().form_valid(form)


class ResumeDetailView(LoginRequiredMixin, UpdateView):
    """View and edit resume details."""
    model = Resume
    form_class = ResumeEditForm
    template_name = 'resumes/resume_detail.html'
    success_url = reverse_lazy('resumes:list')

    def get_queryset(self):
        """Ensure user can only access their own resumes."""
        return Resume.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add parsed data to context."""
        context = super().get_context_data(**kwargs)
        resume = self.object

        # Format parsed data for display
        context['parsed_skills'] = resume.get_parsed_skills_list()
        context['parsed_education'] = resume.get_education_list()
        context['parsed_contact'] = resume.contact_info or {}

        return context


class ResumeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a resume."""
    model = Resume
    template_name = 'resumes/resume_confirm_delete.html'
    success_url = reverse_lazy('resumes:list')

    def get_queryset(self):
        """Ensure user can only delete their own resumes."""
        return Resume.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Delete resume and show success message."""
        messages.success(request, 'Resume deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ResumeDownloadView(LoginRequiredMixin, UpdateView):
    """Download resume file."""
    model = Resume

    def get_queryset(self):
        """Ensure user can only access their own resumes."""
        return Resume.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        """Serve the resume file for download."""
        resume = self.get_object()

        if not resume.file:
            raise Http404("Resume file not found.")

        # Get file content
        try:
            with default_storage.open(resume.file.name, 'rb') as f:
                file_data = f.read()

            # Create response
            response = HttpResponse(
                file_data,
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{resume.original_filename}"'

            return response

        except Exception:
            raise Http404("File could not be served.")


class SetPrimaryResumeView(LoginRequiredMixin, UpdateView):
    """Set a resume as primary."""
    model = Resume
    fields = []  # No form fields needed

    def get_queryset(self):
        """Ensure user can only modify their own resumes."""
        return Resume.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        """Set resume as primary."""
        resume = self.get_object()

        # Set as primary (save method handles the logic)
        resume.is_primary = True
        resume.save()

        messages.success(request, f'"{resume.title}" is now your primary resume.')
        return redirect('resumes:list')


class ResumePreviewView(LoginRequiredMixin, UpdateView):
    """Preview parsed resume content."""
    model = Resume
    template_name = 'resumes/resume_preview.html'

    def get_queryset(self):
        """Ensure user can only access their own resumes."""
        return Resume.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add parsed data to context."""
        context = super().get_context_data(**kwargs)
        resume = self.object

        context['parsed_text'] = resume.parsed_text
        context['parsed_skills'] = resume.get_parsed_skills_list()
        context['parsed_education'] = resume.get_education_list()
        context['parsed_contact'] = resume.contact_info or {}

        return context