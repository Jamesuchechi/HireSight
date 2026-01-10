from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Email Verification
    path('verify-email/notice/', views.VerifyEmailNoticeView.as_view(), name='verify_email_notice'),
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('verify-email/', views.VerifyEmailFormView.as_view(), name='verify_email_form'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    
    # Password Reset
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('forgot-password/done/', views.ForgotPasswordDoneView.as_view(), name='forgot_password_done'),
    path('reset-password/<str:token>/', views.ResetPasswordView.as_view(), name='reset_password'),
    
    # Profile Management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/personal/', views.EditPersonalProfileView.as_view(), name='edit_personal_profile'),
    path('profile/edit/company/', views.EditCompanyProfileView.as_view(), name='edit_company_profile'),
    
    # Public Profiles
    path('profile/<uuid:user_id>/personal/', views.PublicPersonalProfileView.as_view(), name='public_personal_profile'),
    path('profile/<uuid:user_id>/company/', views.PublicCompanyProfileView.as_view(), name='public_company_profile'),
]