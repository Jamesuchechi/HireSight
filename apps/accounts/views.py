from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
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
from datetime import timedelta
import secrets

from .models import User, PersonalProfile, CompanyProfile, EmailVerificationToken, PasswordResetToken
from .forms import (
    RegisterForm, LoginForm, EmailVerificationForm, ForgotPasswordForm, 
    ResetPasswordForm, PersonalProfileForm, CompanyProfileForm
)
from .decorators import personal_required, company_required


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
    """User login view."""
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
        """Log user in."""
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


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Profile'
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


class ProfileView(LoginRequiredMixin, TemplateView):
    """View user profile (redirects to appropriate edit form)."""
    
    def get(self, request):
        """Redirect to appropriate profile edit page."""
        if request.user.account_type == 'personal':
            return redirect('accounts:edit_personal_profile')
        else:
            return redirect('accounts:edit_company_profile')


class EditPersonalProfileView(LoginRequiredMixin, UpdateView):
    """Edit personal (job seeker) profile."""
    model = PersonalProfile
    form_class = PersonalProfileForm
    template_name = 'accounts/edit_personal_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure user has personal account."""
        if request.user.account_type != 'personal':
            messages.error(request, 'This page is only for job seeker accounts.')
            return redirect('dashboard:dashboard_home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """Get current user's profile."""
        return self.request.user.personal_profile
    
    def form_valid(self, form):
        """Save profile."""
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class EditCompanyProfileView(LoginRequiredMixin, UpdateView):
    """Edit company (recruiter) profile."""
    model = CompanyProfile
    form_class = CompanyProfileForm
    template_name = 'accounts/edit_company_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def dispatch(self, request, *args, **kwargs):
        """Ensure user has company account."""
        if request.user.account_type != 'company':
            messages.error(request, 'This page is only for recruiter accounts.')
            return redirect('dashboard:dashboard_home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """Get current user's profile."""
        return self.request.user.company_profile
    
    def form_valid(self, form):
        """Save profile."""
        messages.success(self.request, 'Company profile updated successfully!')
        return super().form_valid(form)


class PublicPersonalProfileView(TemplateView):
    """View public personal profile."""
    template_name = 'accounts/public_personal_profile.html'
    
    def get_context_data(self, **kwargs):
        """Get profile data."""
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        
        user = get_object_or_404(User, id=user_id, account_type='personal')
        profile = user.personal_profile
        
        # Check visibility
        if profile.profile_visibility == 'private':
            if not self.request.user.is_authenticated or self.request.user != user:
                messages.error(self.request, 'This profile is private.')
                return redirect('dashboard:dashboard_home')
        
        context['profile_user'] = user
        context['profile'] = profile
        return context


class PublicCompanyProfileView(TemplateView):
    """View public company profile."""
    template_name = 'accounts/public_company_profile.html'
    
    def get_context_data(self, **kwargs):
        """Get profile data."""
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        
        user = get_object_or_404(User, id=user_id, account_type='company')
        profile = user.company_profile
        
        context['profile_user'] = user
        context['profile'] = profile
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