from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import View, TemplateView, FormView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.sessions.models import Session
from datetime import timedelta
import secrets
import json

from .models import (
    User, PersonalProfile, CompanyProfile, EmailVerificationToken, 
    PasswordResetToken, EmailPreferences, EmailChangeToken, APIKey,
    ProfileView, UserSession, AccountDeletionLog
)

from .forms import (
    RegisterForm, LoginForm, EmailVerificationForm, ForgotPasswordForm,
    ResetPasswordForm, PersonalProfileForm, CompanyProfileForm, EmailPreferencesForm, ChangeEmailForm, CustomPasswordChangeForm, 
    DeleteAccountForm, Enable2FAForm, Verify2FAForm, CreateAPIKeyForm, ResumeImportForm
)
from .decorators import personal_required, company_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from apps.following.models import Follow


class RegisterView(FormView):
    """User registration view."""
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('accounts:verify_email_notice')

    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users to dashboard."""
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard_home')
        
        # Apply rate limiting for POST requests
        if request.method == 'POST':
            from django_ratelimit.core import is_ratelimited
            if is_ratelimited(request, group='register', key='ip', rate='3/h', increment=True):
                return ratelimit_view(request, None)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Save user and send verification email."""
        user = form.save()
        
        # Create verification token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)
        
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # Send verification email
        verification_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:verify_email', kwargs={'token': token})
        )
        
        # Send HTML email
        subject = 'Verify your HireSight email'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email]
        
        # Render HTML content
        html_content = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_url': verification_url,
        })
        
        # Create email message
        email = EmailMultiAlternatives(subject, '', from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
        
        messages.success(
            self.request,
            f'Account created! Please check {user.email} for a verification link.'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Show error messages."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class LoginView(FormView):
    """User login view with 2FA support."""
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard:dashboard_home')

    def get_form_kwargs(self):
        """Pass request to form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users to dashboard."""
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard_home')
        
        # Apply rate limiting for POST requests
        if request.method == 'POST':
            from django_ratelimit.core import is_ratelimited
            if is_ratelimited(request, group='login', key='ip', rate='5/m', increment=True):
                return ratelimit_view(request, None)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Log user in with 2FA check."""
        email = form.cleaned_data.get('username')  # 'username' field contains email
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me', False)
        
        # Authenticate user with request
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
            # Check if user is allowed to login (for Axes)
            from django.contrib.auth.forms import AuthenticationForm
            temp_form = AuthenticationForm()
            temp_form.user_cache = user
            try:
                temp_form.confirm_login_allowed(user)
            except ValidationError as e:
                messages.error(self.request, str(e))
                return self.form_invalid(form)
            
            # Check if 2FA is enabled
            if user.has_2fa_enabled():
                # Store user ID in session and redirect to 2FA verification
                self.request.session['pre_2fa_user_id'] = str(user.id)
                self.request.session['remember_me'] = remember_me
                return redirect('accounts:verify_2fa')
            
            # No 2FA - proceed with normal login
            login(self.request, user)
            
            # Set session expiry
            if not remember_me:
                self.request.session.set_expiry(0)  # Browser close
            else:
                self.request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(self.request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect to next or dashboard
            next_url = self.request.GET.get('next', self.success_url)
            return redirect(next_url)
        else:
            messages.error(self.request, 'Invalid email or password.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Show error messages."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class LogoutView(LoginRequiredMixin, View):
    """User logout view."""
    
    def get(self, request):
        """Log user out and redirect."""
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('dashboard:landing')
    
    def post(self, request):
        """Log user out and redirect."""
        return self.get(request)


class VerifyEmailNoticeView(TemplateView):
    """Email verification notice page."""
    template_name = 'accounts/verify_email_notice.html'


class VerifyEmailView(View):
    """Email verification via token."""
    
    def get(self, request, token):
        """Verify email with token from URL."""
        try:
            verification = EmailVerificationToken.objects.get(token=token)
            
            if verification.is_expired():
                messages.error(request, 'This verification link has expired. Please request a new one.')
                return redirect('accounts:resend_verification')
            
            # Mark user as verified
            user = verification.user
            user.is_verified = True
            user.save()
            
            # Delete token
            verification.delete()
            
            messages.success(request, 'Email verified successfully! You can now log in.')
            return redirect('accounts:login')
            
        except EmailVerificationToken.DoesNotExist:
            messages.error(request, 'Invalid verification link.')
            return redirect('accounts:login')


class VerifyEmailFormView(LoginRequiredMixin, FormView):
    """Email verification via manual token entry."""
    template_name = 'accounts/verify_email.html'
    form_class = EmailVerificationForm
    success_url = reverse_lazy('dashboard:dashboard_home')
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect if already verified."""
        if request.user.is_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('dashboard:dashboard_home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Verify token."""
        token = form.cleaned_data.get('token').upper()
        
        try:
            verification = EmailVerificationToken.objects.get(
                user=self.request.user,
                token=token
            )
            
            if verification.is_expired():
                messages.error(self.request, 'This token has expired. Please request a new one.')
                return self.form_invalid(form)
            
            # Mark user as verified
            self.request.user.is_verified = True
            self.request.user.save()
            
            # Delete token
            verification.delete()
            
            messages.success(self.request, 'Email verified successfully!')
            return super().form_valid(form)
            
        except EmailVerificationToken.DoesNotExist:
            messages.error(self.request, 'Invalid verification token.')
            return self.form_invalid(form)


class ResendVerificationView(LoginRequiredMixin, View):
    """Resend verification email."""
    
    def post(self, request):
        """Send new verification email."""
        if request.user.is_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('dashboard:dashboard_home')
        
        # Delete old tokens
        EmailVerificationToken.objects.filter(user=request.user).delete()
        
        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)
        
        EmailVerificationToken.objects.create(
            user=request.user,
            token=token,
            expires_at=expires_at
        )
        
        # Send email
        verification_url = request.build_absolute_uri(
            reverse_lazy('accounts:verify_email', kwargs={'token': token})
        )
        
        # Send HTML email
        subject = 'Verify your HireSight email'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [request.user.email]
        
        # Render HTML content
        html_content = render_to_string('emails/email_verification.html', {
            'user': request.user,
            'verification_url': verification_url,
        })
        
        # Create email message
        email = EmailMultiAlternatives(subject, '', from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
        
        messages.success(request, 'Verification email sent! Please check your inbox.')
        return redirect('accounts:verify_email_form')


class ForgotPasswordView(FormView):
    """Request password reset."""
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('accounts:forgot_password_done')

    def dispatch(self, request, *args, **kwargs):
        """Handle rate limiting for password reset requests."""
        # Apply rate limiting for POST requests
        if request.method == 'POST':
            from django_ratelimit.core import is_ratelimited
            if is_ratelimited(request, group='forgot_password', key='ip', rate='3/h', increment=True):
                return ratelimit_view(request, None)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Send password reset email."""
        email = form.cleaned_data.get('email')
        
        try:
            user = User.objects.get(email__iexact=email)
            
            # Create reset token
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=1)
            
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Send email
            reset_url = self.request.build_absolute_uri(
                reverse_lazy('accounts:reset_password', kwargs={'token': token})
            )
            
            # Send HTML email
            subject = 'Reset your HireSight password'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]
            
            # Render HTML content
            html_content = render_to_string('emails/password_reset.html', {
                'user': user,
                'reset_url': reset_url,
            })
            
            # Create email message
            email = EmailMultiAlternatives(subject, '', from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
        
        except User.DoesNotExist:
            # Don't reveal if email exists
            pass
        
        return super().form_valid(form)


class ForgotPasswordDoneView(TemplateView):
    """Password reset email sent confirmation."""
    template_name = 'accounts/forgot_password_done.html'


class SettingsView(LoginRequiredMixin, TemplateView):
    """User settings view."""
    template_name = 'accounts/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Account Settings'
        return context



class ResetPasswordView(FormView):
    """Reset password with token."""
    template_name = 'accounts/reset_password.html'
    form_class = ResetPasswordForm
    success_url = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        """Validate token before showing form."""
        token = kwargs.get('token')
        
        try:
            self.reset_token = PasswordResetToken.objects.get(token=token)
            
            if self.reset_token.is_expired():
                messages.error(request, 'This password reset link has expired.')
                return redirect('accounts:forgot_password')
            
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Invalid password reset link.')
            return redirect('accounts:forgot_password')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.reset_token.user
        return kwargs
    
    def form_valid(self, form):
        """Save new password."""
        form.save()
        
        # Delete token
        self.reset_token.delete()
        
        messages.success(self.request, 'Password reset successfully! You can now log in.')
        return super().form_valid(form)


class ProfileRedirectView(LoginRequiredMixin, View):
    """Redirect authenticated users to their own profile detail view."""

    def get(self, request):
        """Show the correct profile based on account type."""
        user_id = request.user.id
        if request.user.account_type == 'company':
            return redirect('accounts:company_profile_view', user_id=user_id)
        return redirect('accounts:personal_profile_view', user_id=user_id)


class EditPersonalProfileView(LoginRequiredMixin, UpdateView):
    """Edit personal (job seeker) profile."""
    model = PersonalProfile
    form_class = PersonalProfileForm
    template_name = 'accounts/profile/edit_personal_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure user has personal account and profile exists."""
        if request.user.account_type != 'personal':
            messages.error(request, 'This page is only for job seeker accounts.')
            return redirect('dashboard:dashboard_home')
        
        # Ensure personal profile exists
        try:
            profile = request.user.personal_profile
        except PersonalProfile.DoesNotExist:
            # Create profile if it doesn't exist
            PersonalProfile.objects.create(
                user=request.user,
                full_name=request.user.email.split('@')[0]
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """Get current user's profile."""
        return self.request.user.personal_profile
    
    def post(self, request, *args, **kwargs):
        """Handle POST request."""
        self.object = self.get_object()
        form = self.get_form()
        
        # Debug: Print form data
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            print(f"Form is invalid. Errors: {form.errors}")
            return self.form_invalid(form)
    
    def form_valid(self, form):
        """Save profile with simple text inputs."""
        try:
            # Save the form first to get the profile instance
            profile = form.save(commit=False)
            
            # Process Skills: prefer structured JSON from the new widget, fall back to comma-separated text
            skills_data = []
            skills_json = self.request.POST.get('skills_json', '').strip()
            if skills_json:
                try:
                    import json
                    parsed = json.loads(skills_json)
                    # Ensure each item has keys 'skill' and 'proficiency'
                    skills_data = []
                    for item in parsed:
                        if isinstance(item, dict) and item.get('skill'):
                            skills_data.append({
                                'skill': str(item.get('skill')).strip(),
                                'proficiency': str(item.get('proficiency') or 'intermediate').strip()
                            })
                except Exception:
                    skills_data = []
            else:
                # Backwards-compatible fallback: comma separated list
                skills_text = self.request.POST.get('skills_text', '').strip()
                if skills_text:
                    skill_list = [s.strip() for s in skills_text.split(',') if s.strip()]
                    skills_data = [{'skill': skill, 'proficiency': 'intermediate'} for skill in skill_list]

            profile.skills = skills_data
            print(f"Saved skills: {skills_data}")
            
            # Process Experience: prefer structured JSON from the new widget, fall back to text parsing
            experience_data = []
            experience_json = self.request.POST.get('experience_json', '').strip()
            if experience_json:
                try:
                    import json
                    parsed = json.loads(experience_json)
                    # Ensure each item has required keys
                    experience_data = []
                    for item in parsed:
                        if isinstance(item, dict):
                            experience_data.append({
                                'role': str(item.get('role', '')).strip(),
                                'company': str(item.get('company', '')).strip(),
                                'start_date': str(item.get('start_date', '')).strip(),
                                'end_date': str(item.get('end_date', '')).strip(),
                                'current': bool(item.get('current', False)),
                                'description': str(item.get('description', '')).strip()
                            })
                except Exception:
                    experience_data = []
            else:
                # Backwards-compatible fallback: parse multi-line text
                experience_text = self.request.POST.get('experience_text', '').strip()
                if experience_text:
                    lines = [line.strip() for line in experience_text.split('\n') if line.strip()]
                    for line in lines:
                        # Parse format: "Role at Company (Year-Year): Description"
                        exp_entry = {'company': '', 'role': '', 'start_date': '', 'end_date': '', 'current': False, 'description': ''}

                        # Split by colon to separate description
                        if ':' in line:
                            main_part, description = line.split(':', 1)
                            exp_entry['description'] = description.strip()
                        else:
                            main_part = line

                        # Extract dates if present (YYYY-YYYY) or (YYYY-Present)
                        import re
                        date_match = re.search(r'\((\d{4})[-–](\d{4}|Present)\)', main_part)
                        if date_match:
                            exp_entry['start_date'] = date_match.group(1)
                            if date_match.group(2).lower() == 'present':
                                exp_entry['current'] = True
                            else:
                                exp_entry['end_date'] = date_match.group(2)
                            main_part = main_part[:date_match.start()].strip()

                        # Split by "at" to get role and company
                        if ' at ' in main_part:
                            role, company = main_part.split(' at ', 1)
                            exp_entry['role'] = role.strip()
                            exp_entry['company'] = company.strip()
                        else:
                            exp_entry['role'] = main_part.strip()

                        if exp_entry['role'] or exp_entry['company']:
                            experience_data.append(exp_entry)

            profile.experience = experience_data
            print(f"Saved experience: {experience_data}")
            
            # Process Education from multi-line text
            education_text = self.request.POST.get('education_text', '').strip()
            education_data = []
            if education_text:
                lines = [line.strip() for line in education_text.split('\n') if line.strip()]
                for line in lines:
                    # Parse format: "Degree in Field, Institution (Year-Year)"
                    edu_entry = {'institution': '', 'degree': '', 'field': '', 'start_year': None, 'end_year': None}
                    
                    # Extract years if present
                    import re
                    year_match = re.search(r'\((\d{4})[-–](\d{4})\)', line)
                    if year_match:
                        try:
                            edu_entry['start_year'] = int(year_match.group(1))
                            edu_entry['end_year'] = int(year_match.group(2))
                        except ValueError:
                            pass
                        line = line[:year_match.start()].strip()
                    
                    # Split by comma to separate institution
                    if ',' in line:
                        degree_part, institution = line.rsplit(',', 1)
                        edu_entry['institution'] = institution.strip()
                        
                        # Split degree part by "in" to get degree and field
                        if ' in ' in degree_part:
                            degree, field = degree_part.split(' in ', 1)
                            edu_entry['degree'] = degree.strip()
                            edu_entry['field'] = field.strip()
                        else:
                            edu_entry['degree'] = degree_part.strip()
                    else:
                        edu_entry['degree'] = line.strip()
                    
                    if edu_entry['degree'] or edu_entry['institution']:
                        education_data.append(edu_entry)
            
            profile.education = education_data
            print(f"Saved education: {education_data}")
            
            # Process Certifications: prefer structured JSON from the new widget
            certifications_data = []
            certifications_json = self.request.POST.get('certifications_json', '').strip()
            if certifications_json:
                try:
                    import json
                    parsed = json.loads(certifications_json)
                    # Ensure each item has required keys
                    certifications_data = []
                    for item in parsed:
                        if isinstance(item, dict):
                            certifications_data.append({
                                'name': str(item.get('name', '')).strip(),
                                'issuer': str(item.get('issuer', '')).strip(),
                                'date': str(item.get('date', '')).strip(),
                                'url': str(item.get('url', '')).strip()
                            })
                except Exception:
                    certifications_data = []
            
            profile.certifications = certifications_data
            print(f"Saved certifications: {certifications_data}")
            
            # Process Portfolio Links: prefer structured JSON from the new widget
            portfolio_links_data = []
            portfolio_links_json = self.request.POST.get('portfolio_links_json', '').strip()
            if portfolio_links_json:
                try:
                    import json
                    parsed = json.loads(portfolio_links_json)
                    # Ensure each item has required keys
                    portfolio_links_data = []
                    for item in parsed:
                        if isinstance(item, dict):
                            portfolio_links_data.append({
                                'type': str(item.get('type', 'website')).strip(),
                                'url': str(item.get('url', '')).strip()
                            })
                except Exception:
                    portfolio_links_data = []
            
            profile.portfolio_links = portfolio_links_data
            print(f"Saved portfolio links: {portfolio_links_data}")
            
            # Save the profile with all data
            profile.save()
            print(f"Profile saved successfully. ID: {profile.id}")
            
            messages.success(self.request, '✨ Profile updated successfully!')
            return redirect(self.success_url)
            
        except Exception as e:
            import traceback
            error_msg = f"Error saving profile: {e}"
            print(error_msg)
            print(traceback.format_exc())
            messages.error(self.request, error_msg)
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        print(f"Form validation failed!")
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")
        
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        context['profile_completion'] = profile.calculate_completion_score()
        
        # Pass JSON data safely to template
        import json
        context['skills_json'] = json.dumps(profile.skills or [])
        context['experience_json'] = json.dumps(profile.experience or [])
        context['education_json'] = json.dumps(profile.education or [])
        context['certifications_json'] = json.dumps(profile.certifications or [])
        context['portfolio_links_json'] = json.dumps(profile.portfolio_links or [])
        context['preferred_job_types'] = json.dumps(profile.preferred_job_types or [])
        
        return context


class ResumeImportView(LoginRequiredMixin, FormView):
    """Import resume data into user profile."""
    template_name = 'accounts/profile/resume_import.html'
    form_class = ResumeImportForm
    success_url = reverse_lazy('accounts:profile')
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure user has personal account."""
        if request.user.account_type != 'personal':
            messages.error(request, 'Resume import is only available for job seeker accounts.')
            return redirect('dashboard:dashboard_home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Process the uploaded resume file."""
        try:
            from apps.resumes.parsers import ResumeParser
            from .utils import map_resume_to_profile_data, merge_profile_data, preview_import_changes
            import tempfile
            import os
            
            resume_file = form.cleaned_data['resume_file']
            import_options = form.cleaned_data.get('import_options', [])
            merge_strategy = form.cleaned_data['merge_strategy']
            
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{resume_file.name}') as temp_file:
                for chunk in resume_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Parse the resume
                parser = ResumeParser()
                parsed_result = parser.parse_file(temp_file_path, resume_file.name)
                
                if not parsed_result.get('success', False):
                    messages.error(self.request, parsed_result.get('error', 'Could not parse the resume file.'))
                    return self.form_invalid(form)
                
                # Map resume data to profile format
                profile_data = map_resume_to_profile_data(parsed_result, import_options)
                
                # Get current profile
                try:
                    profile = self.request.user.personal_profile
                except PersonalProfile.DoesNotExist:
                    profile = PersonalProfile.objects.create(
                        user=self.request.user,
                        full_name=self.request.user.email.split('@')[0]
                    )
                
                if merge_strategy == 'preview':
                    # Show preview of changes
                    changes = preview_import_changes(profile, profile_data)
                    changes = {k.replace('_', ' '): v for k, v in changes.items()}
                    self.request.session['resume_import_preview'] = {
                        'profile_data': profile_data,
                        'changes': changes,
                        'import_options': import_options
                    }
                    messages.info(self.request, 'Preview generated. Review the changes below.')
                    return render(self.request, self.template_name, {
                        'form': form,
                        'preview_data': changes,
                        'profile_data': profile_data
                    })
                
                elif merge_strategy == 'replace':
                    # Replace existing data
                    for field, value in profile_data.items():
                        if field in import_options or not import_options:
                            setattr(profile, field, value)
                    profile.save()
                    messages.success(self.request, 'Resume data imported successfully! Your profile has been updated.')
                
                else:  # merge
                    # Merge with existing data
                    merged_data = merge_profile_data(profile, profile_data, 'smart')
                    for field, value in merged_data.items():
                        setattr(profile, field, value)
                    profile.save()
                    messages.success(self.request, 'Resume data merged successfully! Your profile has been updated.')
                
                return super().form_valid(form)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            import traceback
            print(f"Error importing resume: {e}")
            print(traceback.format_exc())
            messages.error(self.request, f'Error importing resume: {str(e)}')
            return self.form_invalid(form)


# Add this to your views.py file - replace the existing EditCompanyProfileView

class EditCompanyProfileView(LoginRequiredMixin, UpdateView):
    """Edit company (recruiter) profile."""
    model = CompanyProfile
    form_class = CompanyProfileForm
    template_name = 'accounts/profile/edit_company_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure user has company account and profile exists."""
        if request.user.account_type != 'company':
            messages.error(request, 'This page is only for recruiter accounts.')
            return redirect('dashboard:dashboard_home')
        
        # Ensure company profile exists
        try:
            profile = request.user.company_profile
        except CompanyProfile.DoesNotExist:
            # Create profile if it doesn't exist
            CompanyProfile.objects.create(
                user=request.user,
                company_name=request.user.email.split('@')[0]
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """Get current user's profile."""
        return self.request.user.company_profile
    
    def post(self, request, *args, **kwargs):
        """Handle POST request."""
        self.object = self.get_object()
        form = self.get_form()
        
        # Debug: Print form data
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            print(f"Form is invalid. Errors: {form.errors}")
            return self.form_invalid(form)
    
    def form_valid(self, form):
        """Save company profile with structured locations and benefits."""
        try:
            # Save the form first to get the profile instance
            profile = form.save(commit=False)
            
            # Process Benefits from JSON (new chips format) or fallback to textarea
            benefits_json = self.request.POST.get('benefits_json', '').strip()
            benefits_data = []
            
            if benefits_json:
                try:
                    import json
                    benefits_data = json.loads(benefits_json)
                except json.JSONDecodeError:
                    # Fallback to old textarea format for backwards compatibility
                    benefits_text = self.request.POST.get('benefits', '').strip()
                    if benefits_text:
                        benefit_lines = [line.strip() for line in benefits_text.split('\n') if line.strip()]
                        benefits_data = benefit_lines
            else:
                # Fallback to old textarea format for backwards compatibility
                benefits_text = self.request.POST.get('benefits', '').strip()
                if benefits_text:
                    benefit_lines = [line.strip() for line in benefits_text.split('\n') if line.strip()]
                    benefits_data = benefit_lines
            
            profile.benefits = benefits_data
            print(f"Saved benefits: {benefits_data}")
            
            # Process Locations from JSON (new structured format)
            locations_json = self.request.POST.get('locations_json', '').strip()
            locations_data = []
            
            if locations_json:
                try:
                    import json
                    parsed_locations = json.loads(locations_json)
                    
                    # Validate and normalize locations
                    for loc in parsed_locations:
                        if isinstance(loc, dict):
                            # Ensure we have required fields
                            location_entry = {
                                'address': loc.get('address', ''),
                                'city': loc.get('city', ''),
                                'state': loc.get('state', ''),
                                'country': loc.get('country', ''),
                                'postal_code': loc.get('postal_code', ''),
                                'lat': loc.get('lat', 0),
                                'lng': loc.get('lng', 0),
                                'is_hq': bool(loc.get('is_hq', False))
                            }
                            
                            # Only add if we have basic location info
                            if location_entry['city'] and location_entry['country']:
                                locations_data.append(location_entry)
                except json.JSONDecodeError:
                    # Fallback to old text format for backwards compatibility
                    locations_text = self.request.POST.get('locations', '').strip()
                    if locations_text:
                        location_lines = [line.strip() for line in locations_text.split('\n') if line.strip()]
                        for line in location_lines:
                            # Parse format: "City, Country" or "City, Country (Headquarters)"
                            is_hq = '(headquarters)' in line.lower() or '(hq)' in line.lower()
                            
                            # Remove headquarters marker
                            import re
                            clean_line = re.sub(r'\s*\(headquarters\)\s*|\s*\(hq\)\s*', '', line, flags=re.IGNORECASE).strip()
                            
                            # Split by comma to get city and country
                            parts = [p.strip() for p in clean_line.split(',')]
                            city = parts[0] if len(parts) > 0 else ''
                            country = parts[1] if len(parts) > 1 else ''
                            
                            if city:
                                locations_data.append({
                                    'city': city,
                                    'country': country,
                                    'is_hq': is_hq,
                                    'address': '',
                                    'state': '',
                                    'postal_code': '',
                                    'lat': 0,
                                    'lng': 0
                                })
            
            profile.locations = locations_data
            print(f"Saved locations: {locations_data}")
            
            # Process Team Photos upload
            team_photos_data = []
            if 'team_photos' in self.request.FILES:
                # Handle multiple file upload
                team_photos_files = self.request.FILES.getlist('team_photos')
                
                import os
                import uuid
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                
                for photo_file in team_photos_files:
                    # Generate unique filename
                    file_ext = os.path.splitext(photo_file.name)[1]
                    unique_filename = f"team_{uuid.uuid4().hex}{file_ext}"
                    
                    # Save file to media/company_team/
                    file_path = f"company_team/{unique_filename}"
                    
                    # Save the file
                    saved_path = default_storage.save(file_path, ContentFile(photo_file.read()))
                    
                    # Add to team photos data
                    team_photos_data.append({
                        'url': default_storage.url(saved_path),
                        'caption': ''  # Empty caption for now
                    })
                
                print(f"Saved {len(team_photos_data)} team photos")
            
            # Merge with existing team photos if any
            existing_photos = profile.team_photos or []
            profile.team_photos = existing_photos + team_photos_data
            
            # Save the profile with all data
            profile.save()
            print(f"Company profile saved successfully. ID: {profile.id}")
            
            messages.success(self.request, '✨ Company profile updated successfully!')
            return redirect(self.success_url)
            
        except Exception as e:
            import traceback
            error_msg = f"Error saving company profile: {e}"
            print(error_msg)
            print(traceback.format_exc())
            messages.error(self.request, error_msg)
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        print(f"Form validation failed!")
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")
        
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        
        # No need to pass JSON data anymore - template handles it directly
        return context

class PublicPersonalProfileView(TemplateView):
    """View public personal profile with tracking."""
    template_name = 'accounts/profile/personal_profile_view.html'
    
    def dispatch(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        self.profile_user = get_object_or_404(User, id=user_id, account_type='personal')
        try:
            self.profile = self.profile_user.personal_profile
        except PersonalProfile.DoesNotExist:
            raise Http404('Personal profile not found.')

        # Check privacy settings
        if self.profile.profile_visibility == 'private':
            if not request.user.is_authenticated or request.user != self.profile_user:
                messages.error(request, 'This profile is private.')
                return redirect('dashboard:dashboard_home')
        
        # Track profile view (only if not viewing own profile)
        if request.user != self.profile_user:
            self._track_profile_view(request)

        return super().dispatch(request, *args, **kwargs)
    
    def _track_profile_view(self, request):
        """Track profile view for analytics."""
        try:
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if request.user.is_authenticated:
                # Track authenticated view
                ProfileView.objects.create(
                    profile_user=self.profile_user,
                    viewer=request.user,
                    viewer_user_agent=user_agent
                )
            else:
                # Track anonymous view by IP
                ip = request.META.get('REMOTE_ADDR')
                ProfileView.objects.create(
                    profile_user=self.profile_user,
                    viewer_ip=ip,
                    viewer_user_agent=user_agent
                )
        except Exception as e:
            # Don't fail if tracking fails
            print(f"Error tracking profile view: {e}")

    def get_context_data(self, **kwargs):
        """Get profile data."""
        context = super().get_context_data(**kwargs)
        
        context['profile_user'] = self.profile_user
        context['profile'] = self.profile
        context['is_own_profile'] = self.request.user == self.profile_user
        context['applications_count'] = getattr(self.profile_user, 'applications_count', 0)
        context['profile_completion'] = self.profile.calculate_completion_score()
        context['followers_count'] = Follow.get_follower_count(self.profile_user)
        context['following_count'] = Follow.get_following_count(self.profile_user)

        request_user = self.request.user
        is_authenticated = request_user.is_authenticated
        is_personal_requestor = getattr(request_user, 'account_type', None) == 'personal'

        context['is_following'] = (
            is_authenticated and Follow.objects.filter(
                follower=request_user,
                followed=self.profile_user
            ).exists()
        )
        context['follows_you'] = False
        if is_authenticated:
            context['follows_you'] = Follow.objects.filter(
                follower=self.profile_user,
                followed=request_user
            ).exists()
        context['is_mutual_follow'] = context['is_following'] and context['follows_you']
        context['can_follow'] = is_personal_requestor and not context['is_own_profile']
        context['can_view_mutual'] = is_personal_requestor and is_authenticated and not context['is_own_profile']

        # Add view count if viewing own profile
        if context['is_own_profile']:
            context['total_profile_views'] = self.profile_user.get_profile_views_count()
            context['profile_views_this_week'] = self.profile_user.get_profile_views_count(days=7)
        
        return context

class PublicCompanyProfileView(TemplateView):
    """View public company profile with tracking."""
    template_name = 'accounts/profile/company_profile_view.html'
    
    def dispatch(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        self.profile_user = get_object_or_404(User, id=user_id, account_type='company')
        try:
            self.profile = self.profile_user.company_profile
        except CompanyProfile.DoesNotExist:
            raise Http404('Company profile not found.')
        
        # Track profile view (only if not viewing own profile)
        if request.user != self.profile_user:
            self._track_profile_view(request)

        return super().dispatch(request, *args, **kwargs)
    
    def _track_profile_view(self, request):
        """Track profile view for analytics."""
        try:
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if request.user.is_authenticated:
                # Track authenticated view
                ProfileView.objects.create(
                    profile_user=self.profile_user,
                    viewer=request.user,
                    viewer_user_agent=user_agent
                )
            else:
                # Track anonymous view by IP
                ip = request.META.get('REMOTE_ADDR')
                ProfileView.objects.create(
                    profile_user=self.profile_user,
                    viewer_ip=ip,
                    viewer_user_agent=user_agent
                )
        except Exception as e:
            # Don't fail if tracking fails
            print(f"Error tracking profile view: {e}")

    def get_context_data(self, **kwargs):
        """Get profile data."""
        context = super().get_context_data(**kwargs)
        
        context['profile_user'] = self.profile_user
        context['profile'] = self.profile
        context['is_own_profile'] = self.request.user == self.profile_user
        context['active_jobs_count'] = 0  
        context['recent_jobs'] = []  

        request_user = self.request.user
        is_authenticated = request_user.is_authenticated
        is_personal_requestor = getattr(request_user, 'account_type', None) == 'personal'

        context['followers_count'] = Follow.get_follower_count(self.profile_user)
        context['following_count'] = Follow.get_following_count(self.profile_user)
        context['is_following'] = (
            is_authenticated and Follow.objects.filter(
                follower=request_user,
                followed=self.profile_user
            ).exists()
        )
        context['can_follow'] = is_personal_requestor and not context['is_own_profile']
        context['can_view_mutual'] = is_personal_requestor and is_authenticated and not context['is_own_profile']
        
        # Add view count if viewing own profile
        if context['is_own_profile']:
            context['total_profile_views'] = self.profile_user.get_profile_views_count()
            context['profile_views_this_week'] = self.profile_user.get_profile_views_count(days=7)
        
        return context


def ratelimit_view(request, exception):
    """
    View shown when rate limit is exceeded.
    Used by django-ratelimit.
    """
    return render(request, 'errors/rate_limit.html', {
        'exception': exception,
    }, status=429)


def health_check(request):
    """
    Health check endpoint for monitoring.
    Returns JSON with system status.
    """
    from django.db import connection
    from django.core.cache import cache
    import psutil
    import json
    from datetime import datetime

    health_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data['checks']['database'] = 'healthy'
    except Exception as e:
        health_data['checks']['database'] = f'unhealthy: {str(e)}'
        health_data['status'] = 'unhealthy'

    # Cache check
    try:
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_data['checks']['cache'] = 'healthy'
        else:
            health_data['checks']['cache'] = 'unhealthy: cache not working'
            health_data['status'] = 'unhealthy'
    except Exception as e:
        health_data['checks']['cache'] = f'unhealthy: {str(e)}'
        health_data['status'] = 'unhealthy'

    # System resources
    try:
        health_data['system'] = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }
    except ImportError:
        health_data['system'] = {'note': 'psutil not available'}

    status_code = 200 if health_data['status'] == 'healthy' else 503

    return JsonResponse(health_data, status=status_code)


class SavePersonalSkillsView(LoginRequiredMixin, View):
    """AJAX endpoint to save personal profile skills (accepts JSON array)."""

    def post(self, request):
        if request.user.account_type != 'personal':
            return JsonResponse({'ok': False, 'error': 'Not a personal account'}, status=403)

        try:
            import json
            payload = request.POST.get('skills_json') or request.body.decode('utf-8') or ''
            if not payload:
                # empty list
                skills = []
            else:
                # If payload is form-encoded, it will be a JSON string in 'skills_json'
                try:
                    skills = json.loads(payload)
                except Exception:
                    # Try parsing as form encoded
                    skills = json.loads(request.POST.get('skills_json', '[]'))

            # Normalize and validate
            clean = []
            for item in skills:
                if isinstance(item, dict) and item.get('skill'):
                    clean.append({
                        'skill': str(item.get('skill')).strip(),
                        'proficiency': str(item.get('proficiency') or 'intermediate').strip()
                    })

            profile = request.user.personal_profile
            profile.skills = clean
            profile.save()

            return JsonResponse({'ok': True, 'skills': clean})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class AdminCompanyVerificationListView(LoginRequiredMixin, TemplateView):
    """Admin view to list companies pending verification."""
    template_name = 'accounts/admin/company_verification_list.html'
    
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get companies pending verification
        pending_companies = CompanyProfile.objects.filter(verification_status='pending')
        verified_companies = CompanyProfile.objects.filter(verification_status='verified')
        
        context['pending_companies'] = pending_companies
        context['verified_companies'] = verified_companies
        context['title'] = 'Company Verification Review'
        
        return context


class AdminCompanyVerificationDetailView(LoginRequiredMixin, TemplateView):
    """Admin view to review a specific company's verification documents."""
    template_name = 'accounts/admin/company_verification_detail.html'
    
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        company_id = kwargs.get('company_id')
        company_profile = get_object_or_404(CompanyProfile, id=company_id)
        
        context['company_profile'] = company_profile
        context['title'] = f'Review {company_profile.company_name}'
        
        return context


class AdminCompanyVerificationActionView(LoginRequiredMixin, View):
    """Admin view to approve or reject company verification."""
    
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, company_id):
        company_profile = get_object_or_404(CompanyProfile, id=company_id)
        action = request.POST.get('action')  # 'approve' or 'reject'
        
        if action == 'approve':
            company_profile.verification_status = 'verified'
            company_profile.save()
            
            # Send notification to company
            self._send_verification_notification(company_profile, approved=True)
            
            messages.success(request, f'{company_profile.company_name} has been verified successfully!')
            
        elif action == 'reject':
            company_profile.verification_status = 'unverified'
            company_profile.save()
            
            # Send notification to company
            self._send_verification_notification(company_profile, approved=False)
            
            messages.success(request, f'{company_profile.company_name} verification has been rejected.')
        
        return redirect('accounts:admin_verification_list')
    
    def _send_verification_notification(self, company_profile, approved=True):
        """Send email notification about verification status change."""
        try:
            user = company_profile.user
            subject = ''
            template_name = ''
            
            if approved:
                subject = f'Your {company_profile.company_name} account has been verified!'
                template_name = 'accounts/emails/company_verification_approved.html'
            else:
                subject = f'Your {company_profile.company_name} verification request'
                template_name = 'accounts/emails/company_verification_rejected.html'
            
            # Render HTML content
            html_content = render_to_string(template_name, {
                'company': company_profile,
                'approved': approved,
            })
            
            # Create email message
            email = EmailMultiAlternatives(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error sending verification notification to {user.email}: {e}")


class SavePersonalEducationView(LoginRequiredMixin, View):
    """AJAX endpoint to save personal profile education (accepts JSON array)."""

    def post(self, request):
        if request.user.account_type != 'personal':
            return JsonResponse({'ok': False, 'error': 'Not a personal account'}, status=403)

        try:
            import json
            payload = request.POST.get('education_json') or request.body.decode('utf-8') or ''
            if not payload:
                # empty list
                education = []
            else:
                # If payload is form-encoded, it will be a JSON string in 'education_json'
                try:
                    education = json.loads(payload)
                except Exception:
                    # Try parsing as form encoded
                    education = json.loads(request.POST.get('education_json', '[]'))

            # Normalize and validate
            clean = []
            for item in education:
                if isinstance(item, dict):
                    clean.append({
                        'institution': str(item.get('institution', '')).strip(),
                        'degree': str(item.get('degree', '')).strip(),
                        'field': str(item.get('field', '')).strip(),
                        'start_year': str(item.get('start_year', '')).strip(),
                        'end_year': str(item.get('end_year', '')).strip()
                    })

            profile = request.user.personal_profile
            profile.education = clean
            profile.save()

            return JsonResponse({'ok': True, 'education': clean})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class SavePersonalExperienceView(LoginRequiredMixin, View):
    """AJAX endpoint to save personal profile experience (accepts JSON array)."""

    def post(self, request):
        if request.user.account_type != 'personal':
            return JsonResponse({'ok': False, 'error': 'Not a personal account'}, status=403)

        try:
            import json
            payload = request.POST.get('experience_json') or request.body.decode('utf-8') or ''
            if not payload:
                # empty list
                experience = []
            else:
                # If payload is form-encoded, it will be a JSON string in 'experience_json'
                try:
                    experience = json.loads(payload)
                except Exception:
                    # Try parsing as form encoded
                    experience = json.loads(request.POST.get('experience_json', '[]'))

            # Normalize and validate
            clean = []
            for item in experience:
                if isinstance(item, dict):
                    clean.append({
                        'role': str(item.get('role', '')).strip(),
                        'company': str(item.get('company', '')).strip(),
                        'start_date': str(item.get('start_date', '')).strip(),
                        'end_date': str(item.get('end_date', '')).strip(),
                        'current': bool(item.get('current', False)),
                        'description': str(item.get('description', '')).strip()
                    })

            profile = request.user.personal_profile
            profile.experience = clean
            profile.save()

            return JsonResponse({'ok': True, 'experience': clean})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class SavePersonalCertificationsView(LoginRequiredMixin, View):
    """AJAX endpoint to save personal profile certifications (accepts JSON array)."""

    def post(self, request):
        if request.user.account_type != 'personal':
            return JsonResponse({'ok': False, 'error': 'Not a personal account'}, status=403)

        try:
            import json
            payload = request.POST.get('certifications_json') or request.body.decode('utf-8') or ''
            if not payload:
                # empty list
                certifications = []
            else:
                # If payload is form-encoded, it will be a JSON string in 'certifications_json'
                try:
                    certifications = json.loads(payload)
                except Exception:
                    # Try parsing as form encoded
                    certifications = json.loads(request.POST.get('certifications_json', '[]'))

            # Normalize and validate
            clean = []
            for item in certifications:
                if isinstance(item, dict) and item.get('name'):
                    clean.append({
                        'name': str(item.get('name')).strip(),
                        'issuer': str(item.get('issuer') or '').strip(),
                        'date': str(item.get('date') or '').strip(),
                        'url': str(item.get('url') or '').strip()
                    })

            profile = request.user.personal_profile
            profile.certifications = clean
            profile.save()

            return JsonResponse({'ok': True, 'certifications': clean})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class SavePersonalPortfolioLinksView(LoginRequiredMixin, View):
    """AJAX endpoint to save personal profile portfolio links (accepts JSON array)."""

    def post(self, request):
        if request.user.account_type != 'personal':
            return JsonResponse({'ok': False, 'error': 'Not a personal account'}, status=403)

        try:
            import json
            payload = request.POST.get('portfolio_links_json') or request.body.decode('utf-8') or ''
            if not payload:
                # empty list
                portfolio_links = []
            else:
                # If payload is form-encoded, it will be a JSON string in 'portfolio_links_json'
                try:
                    portfolio_links = json.loads(payload)
                except Exception:
                    # Try parsing as form encoded
                    portfolio_links = json.loads(request.POST.get('portfolio_links_json', '[]'))

            # Normalize and validate
            clean = []
            for item in portfolio_links:
                if isinstance(item, dict) and item.get('url'):
                    clean.append({
                        'type': str(item.get('type') or 'website').strip(),
                        'url': str(item.get('url')).strip()
                    })

            profile = request.user.personal_profile
            profile.portfolio_links = clean
            profile.save()

            return JsonResponse({'ok': True, 'portfolio_links': clean})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class EmailPreferencesView(LoginRequiredMixin, TemplateView):
    """View email notification preferences."""
    template_name = 'accounts/settings/email_preferences.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email_preferences'] = self.request.user.email_preferences
        context['form'] = EmailPreferencesForm(instance=self.request.user.email_preferences)
        context['title'] = 'Email Preferences'
        return context


class UpdateEmailPreferencesView(LoginRequiredMixin, FormView):
    """Update email notification preferences."""
    form_class = EmailPreferencesForm
    template_name = 'accounts/settings/email_preferences.html'
    success_url = reverse_lazy('accounts:email_preferences')
    
    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user.email_preferences
        return kwargs
    
    def form_valid(self, form):
        """Save preferences."""
        form.save()
        messages.success(self.request, '✅ Email preferences updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Email Preferences'
        return context


class ChangeEmailView(LoginRequiredMixin, FormView):
    """View for requesting email change."""
    template_name = 'accounts/settings/change_email.html'
    form_class = ChangeEmailForm
    success_url = reverse_lazy('accounts:change_email')
    
    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Create email change token and send verification email."""
        new_email = form.cleaned_data.get('new_email')
        
        # Delete any existing email change tokens for this user
        EmailChangeToken.objects.filter(user=self.request.user).delete()
        
        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)
        
        EmailChangeToken.objects.create(
            user=self.request.user,
            new_email=new_email,
            token=token,
            expires_at=expires_at
        )
        
        # Send verification email to NEW email address
        verification_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:confirm_change_email', kwargs={'token': token})
        )
        
        # Send HTML email
        subject = 'Confirm your email change - HireSight'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [new_email]
        
        # Render HTML content
        html_content = render_to_string('emails/email_change_verification.html', {
            'user': self.request.user,
            'new_email': new_email,
            'verification_url': verification_url,
        })
        
        # Create email message
        email = EmailMultiAlternatives(subject, '', from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
        
        messages.success(
            self.request,
            f'Email change request sent! Please check {new_email} for a confirmation link.'
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Change Email Address'
        return context


class ConfirmChangeEmailView(View):
    """Confirm email change with token."""
    
    def get(self, request, token):
        """Confirm email change with token."""
        try:
            change_token = EmailChangeToken.objects.get(token=token)
            
            if change_token.is_expired():
                messages.error(request, 'This email change link has expired. Please request a new one.')
                return redirect('accounts:change_email')
            
            # Update user's email
            old_email = change_token.user.email
            new_email = change_token.new_email
            
            change_token.user.email = new_email
            change_token.user.save()
            
            # Delete token
            change_token.delete()
            
            # Send confirmation email to OLD email address
            subject = 'Your email address has been changed - HireSight'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [old_email]
            
            html_content = render_to_string('emails/email_change_notification.html', {
                'user': change_token.user,
                'old_email': old_email,
                'new_email': new_email,
            })
            
            email = EmailMultiAlternatives(subject, '', from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
            
            messages.success(
                request,
                f'Email successfully changed to {new_email}! A confirmation has been sent to your old email address.'
            )
            
            return redirect('accounts:settings')
            
        except EmailChangeToken.DoesNotExist:
            messages.error(request, 'Invalid email change link.')
            return redirect('accounts:change_email')




# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

class ChangePasswordView(LoginRequiredMixin, FormView):
    """Change password while logged in."""
    template_name = 'accounts/settings/change_password.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('accounts:settings')
    
    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Save new password and keep user logged in."""
        form.save()
        # Keep user logged in after password change
        update_session_auth_hash(self.request, form.user)
        
        # Send notification email
        self._send_password_change_notification()
        
        messages.success(self.request, '✅ Password changed successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Show error messages."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)
    
    def _send_password_change_notification(self):
        """Send email notification about password change."""
        try:
            subject = 'Your password has been changed - HireSight'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [self.request.user.email]
            
            html_content = render_to_string('emails/password_changed.html', {
                'user': self.request.user,
                'timestamp': timezone.now(),
            })
            
            email = EmailMultiAlternatives(subject, '', from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
        except Exception as e:
            print(f"Error sending password change notification: {e}")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Change Password'
        return context


# ============================================================================
# ACCOUNT DELETION & DATA EXPORT
# ============================================================================

class ExportDataView(LoginRequiredMixin, View):
    """Export user data as JSON (GDPR compliance)."""
    
    def get(self, request):
        user = request.user
        
        # Gather all user data
        data = {
            'export_date': timezone.now().isoformat(),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'account_type': user.account_type,
                'created_at': user.created_at.isoformat(),
                'is_verified': user.is_verified,
                'two_factor_enabled': user.two_factor_enabled,
            },
            'profile': {},
            'email_preferences': {},
            'api_keys': [],
            'profile_views': [],
            'sessions': [],
        }
        
        # Add profile data
        if user.account_type == 'personal' and hasattr(user, 'personal_profile'):
            profile = user.personal_profile
            data['profile'] = {
                'full_name': profile.full_name,
                'headline': profile.headline,
                'location': profile.location,
                'phone': profile.phone,
                'bio': profile.bio,
                'skills': profile.skills or [],
                'experience': profile.experience or [],
                'education': profile.education or [],
                'certifications': profile.certifications or [],
                'portfolio_links': profile.portfolio_links or [],
                'preferred_job_types': profile.preferred_job_types or [],
                'remote_preference': profile.remote_preference,
                'salary_expectation_min': profile.salary_expectation_min,
                'salary_expectation_max': profile.salary_expectation_max,
                'salary_currency': profile.salary_currency,
                'availability': profile.availability,
                'profile_visibility': profile.profile_visibility,
                'created_at': profile.created_at.isoformat(),
            }
        elif user.account_type == 'company' and hasattr(user, 'company_profile'):
            profile = user.company_profile
            data['profile'] = {
                'company_name': profile.company_name,
                'industry': profile.industry,
                'company_size': profile.company_size,
                'locations': profile.locations or [],
                'website': profile.website,
                'description': profile.description,
                'mission': profile.mission,
                'culture': profile.culture,
                'benefits': profile.benefits or [],
                'founded_year': profile.founded_year,
                'verification_status': profile.verification_status,
                'created_at': profile.created_at.isoformat(),
            }
        
        # Add email preferences
        if hasattr(user, 'email_preferences'):
            prefs = user.email_preferences
            data['email_preferences'] = {
                'email_frequency': prefs.email_frequency,
                'enabled_notifications': list(prefs.get_enabled_notifications()),
            }
        
        # Add API keys (masked)
        data['api_keys'] = [
            {
                'name': key.name,
                'key_prefix': key.key_prefix,
                'created_at': key.created_at.isoformat(),
                'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
                'is_active': key.is_active,
            }
            for key in user.api_keys.all()
        ]
        
        # Add profile views (recent 100)
        data['profile_views'] = [
            {
                'viewer': view.viewer.get_full_name() if view.viewer else 'Anonymous',
                'viewed_at': view.viewed_at.isoformat(),
            }
            for view in user.profile_views_received.all()[:100]
        ]
        
        # Add active sessions
        data['sessions'] = [
            {
                'device_type': session.device_type,
                'location': session.location,
                'ip_address': session.ip_address,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
            }
            for session in user.user_sessions.filter(expires_at__gte=timezone.now())
        ]
        
        # Create JSON response
        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="hiresight_data_{user.id}.json"'
        
        return response


class DeleteAccountView(LoginRequiredMixin, FormView):
    """Delete user account with confirmation."""
    template_name = 'accounts/settings/delete_account.html'
    form_class = DeleteAccountForm
    success_url = reverse_lazy('dashboard:landing')
    
    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Delete the user account."""
        user = self.request.user
        
        # Log the deletion
        AccountDeletionLog.objects.create(
            user_email=user.email,
            account_type=user.account_type,
            deletion_reason=form.cleaned_data.get('deletion_reason', ''),
            account_age_days=(timezone.now() - user.created_at).days,
            deleted_by_user=True,
        )
        
        # Send goodbye email
        self._send_deletion_confirmation_email(user)
        
        # Logout user
        logout(self.request)
        
        # Delete user (CASCADE will handle related objects)
        user.delete()
        
        messages.success(
            self.request,
            'Your account has been permanently deleted. We\'re sorry to see you go!'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Show error messages."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)
    
    def _send_deletion_confirmation_email(self, user):
        """Send confirmation email about account deletion."""
        try:
            subject = 'Your HireSight account has been deleted'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]
            
            html_content = render_to_string('emails/account_deleted.html', {
                'user': user,
                'deleted_at': timezone.now(),
            })
            
            email = EmailMultiAlternatives(subject, '', from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
        except Exception as e:
            print(f"Error sending deletion confirmation: {e}")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Account'
        return context


# ============================================================================
# TWO-FACTOR AUTHENTICATION (2FA)
# ============================================================================

class Enable2FAView(LoginRequiredMixin, TemplateView):
    """Enable two-factor authentication."""
    template_name = 'accounts/settings/enable_2fa.html'
    
    def get(self, request):
        """Show QR code and setup form."""
        try:
            from django_otp.plugins.otp_totp.models import TOTPDevice
            import qrcode
            import io
            import base64
            
            # Get or create TOTP device
            device, created = TOTPDevice.objects.get_or_create(
                user=request.user,
                name='default',
                defaults={'confirmed': False}
            )
            
            # If device already confirmed, redirect
            if device.confirmed:
                messages.info(request, '2FA is already enabled.')
                return redirect('accounts:settings')
            
            # Generate QR code
            url = device.config_url
            qr = qrcode.make(url)
            buffer = io.BytesIO()
            qr.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return render(request, self.template_name, {
                'qr_code': qr_base64,
                'secret_key': device.key,
                'form': Enable2FAForm(),
                'title': 'Enable Two-Factor Authentication',
            })
            
        except ImportError:
            messages.error(request, '2FA is not available on this system.')
            return redirect('accounts:settings')
    
    def post(self, request):
        """Verify token and enable 2FA."""
        try:
            from django_otp.plugins.otp_totp.models import TOTPDevice
            
            form = Enable2FAForm(request.POST)
            if form.is_valid():
                token = form.cleaned_data['token']
                device = TOTPDevice.objects.get(user=request.user, name='default')
                
                if device.verify_token(token):
                    device.confirmed = True
                    device.save()
                    request.user.two_factor_enabled = True
                    request.user.save()
                    
                    messages.success(request, '✅ Two-factor authentication enabled successfully!')
                    return redirect('accounts:settings')
                else:
                    messages.error(request, '❌ Invalid verification code. Please try again.')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
            
            return self.get(request)
            
        except ImportError:
            messages.error(request, '2FA is not available on this system.')
            return redirect('accounts:settings')


class Disable2FAView(LoginRequiredMixin, View):
    """Disable two-factor authentication."""
    
    def post(self, request):
        """Disable 2FA for user."""
        try:
            from django_otp.plugins.otp_totp.models import TOTPDevice
            
            # Delete all TOTP devices
            TOTPDevice.objects.filter(user=request.user).delete()
            
            # Update user flag
            request.user.two_factor_enabled = False
            request.user.save()
            
            messages.success(request, '2FA has been disabled.')
            return redirect('accounts:settings')
            
        except ImportError:
            messages.error(request, '2FA is not available on this system.')
            return redirect('accounts:settings')


class Verify2FAView(FormView):
    """Verify 2FA token during login."""
    template_name = 'accounts/verify_2fa.html'
    form_class = Verify2FAForm
    success_url = reverse_lazy('dashboard:dashboard_home')
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure user is in pre-2FA state."""
        if 'pre_2fa_user_id' not in request.session:
            messages.warning(request, 'Please log in first.')
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Verify token and log user in."""
        try:
            from django_otp.plugins.otp_totp.models import TOTPDevice
            
            user_id = self.request.session.get('pre_2fa_user_id')
            user = User.objects.get(id=user_id)
            token = form.cleaned_data['token']
            
            device = TOTPDevice.objects.get(user=user, confirmed=True)
            if device.verify_token(token):
                # Login successful
                login(self.request, user)
                del self.request.session['pre_2fa_user_id']
                
                messages.success(self.request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect to next or dashboard
                next_url = self.request.GET.get('next', self.success_url)
                return redirect(next_url)
            else:
                messages.error(self.request, '❌ Invalid verification code.')
                return self.form_invalid(form)
                
        except Exception as e:
            messages.error(self.request, 'An error occurred. Please try again.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Two-Factor Authentication'
        return context


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class ActiveSessionsView(LoginRequiredMixin, TemplateView):
    """View and manage active sessions."""
    template_name = 'accounts/settings/sessions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's active sessions
        sessions = self.request.user.user_sessions.filter(
            expires_at__gte=timezone.now()
        ).order_by('-last_activity')
        
        # Mark current session
        current_session_key = self.request.session.session_key
        for session in sessions:
            session.is_current_session = session.session_key == current_session_key
        
        context['sessions'] = sessions
        context['total_sessions'] = sessions.count()
        context['title'] = 'Active Sessions'
        
        return context


class LogoutAllSessionsView(LoginRequiredMixin, View):
    """Logout from all sessions except current."""
    
    def post(self, request):
        """Delete all other sessions."""
        current_session_key = request.session.session_key
        
        # Delete all other user sessions
        deleted_count = 0
        for session in request.user.user_sessions.filter(expires_at__gte=timezone.now()):
            if session.session_key != current_session_key:
                # Delete Django session
                try:
                    Session.objects.filter(session_key=session.session_key).delete()
                except Session.DoesNotExist:
                    pass
                
                # Delete UserSession record
                session.delete()
                deleted_count += 1
        
        messages.success(
            request,
            f'✅ Logged out from {deleted_count} other device(s). Your current session remains active.'
        )
        return redirect('accounts:active_sessions')


class LogoutSessionView(LoginRequiredMixin, View):
    """Logout from a specific session."""
    
    def post(self, request, session_id):
        """Delete specific session."""
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user
            )
            
            # Prevent logging out current session via this method
            if session.session_key == request.session.session_key:
                messages.error(request, 'Cannot logout your current session this way. Use the main logout instead.')
                return redirect('accounts:active_sessions')
            
            # Delete Django session
            try:
                Session.objects.filter(session_key=session.session_key).delete()
            except Session.DoesNotExist:
                pass
            
            # Delete UserSession record
            session.delete()
            
            messages.success(request, '✅ Session terminated successfully.')
            
        except UserSession.DoesNotExist:
            messages.error(request, 'Session not found.')
        
        return redirect('accounts:active_sessions')


# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

class APIKeysView(LoginRequiredMixin, TemplateView):
    """View and manage API keys."""
    template_name = 'accounts/settings/api_keys.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['api_keys'] = self.request.user.api_keys.filter(is_active=True)
        context['form'] = CreateAPIKeyForm()
        context['title'] = 'API Keys'
        return context


class CreateAPIKeyView(LoginRequiredMixin, FormView):
    """Create a new API key."""
    form_class = CreateAPIKeyForm
    success_url = reverse_lazy('accounts:api_keys')
    
    def form_valid(self, form):
        """Create API key."""
        name = form.cleaned_data['name']
        
        # Generate key
        key_string = APIKey.generate_key()
        
        # Create API key
        api_key = APIKey.objects.create(
            user=self.request.user,
            name=name,
            key=key_string
        )
        
        # Store full key in session to display once
        self.request.session['new_api_key'] = key_string
        self.request.session['new_api_key_name'] = name
        
        messages.success(
            self.request,
            f'✅ API key "{name}" created successfully! Make sure to copy it now - you won\'t see it again.'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Show error messages."""
        for error in form.errors.values():
            messages.error(self.request, error)
        return redirect('accounts:api_keys')


class DeleteAPIKeyView(LoginRequiredMixin, View):
    """Delete an API key."""
    
    def post(self, request, key_id):
        """Soft delete API key."""
        try:
            api_key = APIKey.objects.get(id=key_id, user=request.user)
            api_key.is_active = False
            api_key.save()
            
            messages.success(request, f'✅ API key "{api_key.name}" has been deleted.')
            
        except APIKey.DoesNotExist:
            messages.error(request, 'API key not found.')
        
        return redirect('accounts:api_keys')


# ============================================================================
# PROFILE ANALYTICS
# ============================================================================

class ProfileAnalyticsView(LoginRequiredMixin, TemplateView):
    """View profile analytics and insights."""
    template_name = 'accounts/analytics/profile_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get recent profile views
        views = ProfileView.objects.filter(
            profile_user=self.request.user
        ).select_related('viewer').order_by('-viewed_at')[:50]
        
        # Calculate stats
        total_views = ProfileView.objects.filter(profile_user=self.request.user).count()
        views_today = ProfileView.objects.filter(
            profile_user=self.request.user,
            viewed_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
        views_this_week = ProfileView.objects.filter(
            profile_user=self.request.user,
            viewed_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        views_this_month = ProfileView.objects.filter(
            profile_user=self.request.user,
            viewed_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Get unique viewers
        unique_viewers = ProfileView.objects.filter(
            profile_user=self.request.user,
            viewer__isnull=False
        ).values('viewer').distinct().count()
        
        context['recent_views'] = views
        context['total_views'] = total_views
        context['views_today'] = views_today
        context['views_this_week'] = views_this_week
        context['views_this_month'] = views_this_month
        context['unique_viewers'] = unique_viewers
        context['title'] = 'Profile Analytics'
        
        return context
