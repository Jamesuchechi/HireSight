from django.urls import path
from . import views
from . import i18n_views

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
    
    # Password Management
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('forgot-password/done/', views.ForgotPasswordDoneView.as_view(), name='forgot_password_done'),
    path('reset-password/<str:token>/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('settings/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Profile Management
    path('profile/', views.ProfileRedirectView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('profile/edit/personal/', views.EditPersonalProfileView.as_view(), name='edit_personal_profile'),
    path('profile/edit/company/', views.EditCompanyProfileView.as_view(), name='edit_company_profile'),
    path('profile/import-resume/', views.ResumeImportView.as_view(), name='import_resume'),
    
    # AJAX/API endpoints for profile editing
    path('api/profile/skills/save/', views.SavePersonalSkillsView.as_view(), name='api_save_skills'),
    path('api/profile/experience/save/', views.SavePersonalExperienceView.as_view(), name='api_save_experience'),
    path('api/profile/education/save/', views.SavePersonalEducationView.as_view(), name='api_save_education'),
    path('api/profile/certifications/save/', views.SavePersonalCertificationsView.as_view(), name='api_save_certifications'),
    path('api/profile/portfolio-links/save/', views.SavePersonalPortfolioLinksView.as_view(), name='api_save_portfolio_links'),
    
    # Public Profiles
    path('profile/<uuid:user_id>/personal/', views.PublicPersonalProfileView.as_view(), name='personal_profile_view'),
    path('profile/<uuid:user_id>/company/', views.PublicCompanyProfileView.as_view(), name='company_profile_view'),
    
    # Email Preferences
    path('settings/email-preferences/', views.EmailPreferencesView.as_view(), name='email_preferences'),
    path('settings/email-preferences/update/', views.UpdateEmailPreferencesView.as_view(), name='update_email_preferences'),
    
    # Email Change
    path('settings/change-email/', views.ChangeEmailView.as_view(), name='change_email'),
    path('settings/confirm-change-email/<str:token>/', views.ConfirmChangeEmailView.as_view(), name='confirm_change_email'),
    
    # Language Settings
    path('set-language/', i18n_views.SetLanguageView.as_view(), name='set_language'),
    path('api/language/', i18n_views.LanguageAPIView.as_view(), name='api_language'),
    
    # Account Deletion & Data Export
    path('settings/export-data/', views.ExportDataView.as_view(), name='export_data'),
    path('settings/delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),
    
    # Two-Factor Authentication (2FA)
    path('settings/2fa/enable/', views.Enable2FAView.as_view(), name='enable_2fa'),
    path('settings/2fa/disable/', views.Disable2FAView.as_view(), name='disable_2fa'),
    path('verify-2fa/', views.Verify2FAView.as_view(), name='verify_2fa'),
    
    # Session Management
    path('settings/sessions/', views.ActiveSessionsView.as_view(), name='active_sessions'),
    path('settings/sessions/logout-all/', views.LogoutAllSessionsView.as_view(), name='logout_all_sessions'),
    path('settings/sessions/<uuid:session_id>/logout/', views.LogoutSessionView.as_view(), name='logout_session'),
    
    # API Key Management
    path('settings/api-keys/', views.APIKeysView.as_view(), name='api_keys'),
    path('settings/api-keys/create/', views.CreateAPIKeyView.as_view(), name='create_api_key'),
    path('settings/api-keys/<uuid:key_id>/delete/', views.DeleteAPIKeyView.as_view(), name='delete_api_key'),
    
    # Profile Analytics
    path('analytics/profile-views/', views.ProfileAnalyticsView.as_view(), name='profile_analytics'),
    
    # Admin Verification
    path('admin/verification/', views.AdminCompanyVerificationListView.as_view(), name='admin_verification_list'),
    path('admin/verification/<uuid:company_id>/', views.AdminCompanyVerificationDetailView.as_view(), name='admin_verification_detail'),
    path('admin/verification/<uuid:company_id>/action/', views.AdminCompanyVerificationActionView.as_view(), name='admin_verification_action'),
    
    # Monitoring
    path('health/', views.health_check, name='health_check'),
]