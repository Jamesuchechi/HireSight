from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import View, TemplateView, FormView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.mail import send_mail
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
            return redirect('dashboard:index')
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
        
        send_mail(
            subject='Verify your HireSight email',
            message=f'Click the link to verify your email: {verification_url}\n\nThis link expires in 24 hours.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        
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
    success_url = reverse_lazy('dashboard:index')
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users to dashboard."""
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Log user in."""
        email = form.cleaned_data.get('username')  # 'username' field contains email
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me', False)
        
        # Authenticate user
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
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
    success_url = reverse_lazy('dashboard:index')
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect if already verified."""
        if request.user.is_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('dashboard:index')
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
            return redirect('dashboard:index')
        
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
        
        send_mail(
            subject='Verify your HireSight email',
            message=f'Click the link to verify your email: {verification_url}\n\nThis link expires in 24 hours.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )
        
        messages.success(request, 'Verification email sent! Please check your inbox.')
        return redirect('accounts:verify_email_form')


class ForgotPasswordView(FormView):
    """Request password reset."""
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('accounts:forgot_password_done')
    
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
            
            send_mail(
                subject='Reset your HireSight password',
                message=f'Click the link to reset your password: {reset_url}\n\nThis link expires in 1 hour.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        
        except User.DoesNotExist:
            # Don't reveal if email exists
            pass
        
        return super().form_valid(form)


class ForgotPasswordDoneView(TemplateView):
    """Password reset email sent confirmation."""
    template_name = 'accounts/forgot_password_done.html'


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
            return redirect('dashboard:index')
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
            return redirect('dashboard:index')
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
                return redirect('dashboard:index')
        
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