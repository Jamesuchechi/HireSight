# HireSight Accounts App - Complete Setup Guide

**Created**: January 2026  
**Files**: 5 Python files (managers, forms, views, urls + models from before)

---

## 📁 Files Created

### 1. **accounts_managers.py** → `apps/accounts/managers.py`
Custom user manager for email-based authentication.

**Key Features:**
- `create_user()` - Create regular user with email & password
- `create_superuser()` - Create admin user with elevated privileges
- `get_by_natural_key()` - Lookup user by email (case-insensitive)
- Helper querysets: `personal_users()`, `company_users()`, `verified_users()`, `active_users()`

**Usage:**
```python
# Create regular user
user = User.objects.create_user(
    email='john@example.com',
    password='securepass123',
    account_type='personal'
)

# Create superuser
admin = User.objects.create_superuser(
    email='admin@hiresight.com',
    password='adminpass'
)

# Query helpers
job_seekers = User.objects.personal_users()
recruiters = User.objects.company_users()
verified = User.objects.verified_users()
```

---

### 2. **accounts_forms.py** → `apps/accounts/forms.py`
All forms with Tailwind CSS styling built-in.

**Forms Included:**

#### **Authentication Forms:**
1. **RegisterForm** - User registration
   - Fields: email, account_type (radio), password1, password2, terms_accepted
   - Validates email uniqueness
   - Lowercases email before saving

2. **LoginForm** - User login
   - Fields: email (username), password, remember_me
   - Remember me sets session to 2 weeks

3. **EmailVerificationForm** - Token entry
   - Field: token (uppercase, monospace, centered)

4. **ForgotPasswordForm** - Request password reset
   - Field: email

5. **ResetPasswordForm** - Set new password
   - Fields: new_password1, new_password2

#### **Profile Forms:**
6. **PersonalProfileForm** - Edit job seeker profile
   - Fields: full_name, headline, avatar, location, phone, bio
   - Fields: salary_expectation_min/max, salary_currency
   - Fields: availability, profile_visibility

7. **CompanyProfileForm** - Edit recruiter profile
   - Fields: company_name, logo, industry, company_size
   - Fields: website, description, mission, culture
   - Field: founded_year

#### **Dynamic Forms (for AJAX):**
8. **SkillForm** - Add single skill
   - Fields: skill, proficiency (beginner/intermediate/advanced/expert)

9. **ExperienceForm** - Add work experience
   - Fields: company, role, start_date, end_date, current, description

10. **EducationForm** - Add education
    - Fields: institution, degree, field, start_year, end_year

**All forms have:**
- Tailwind CSS classes pre-applied
- Rounded-xl inputs with focus states
- Proper placeholders
- Accessibility attributes

---

### 3. **accounts_views.py** → `apps/accounts/views.py`
Class-based views for all authentication and profile operations.

**Views Included:**

#### **Authentication Views:**

1. **RegisterView** (FormView)
   - URL: `/accounts/register/`
   - Creates user account
   - Sends verification email with 24-hour token
   - Redirects to verify_email_notice
   - Shows success message

2. **LoginView** (FormView)
   - URL: `/accounts/login/`
   - Authenticates user
   - Handles "remember me" (2 weeks vs browser close)
   - Supports `?next=` redirect parameter
   - Shows welcome message

3. **LogoutView** (View)
   - URL: `/accounts/logout/`
   - Logs user out
   - Shows info message
   - Redirects to landing page

#### **Email Verification Views:**

4. **VerifyEmailNoticeView** (TemplateView)
   - URL: `/accounts/verify-email/notice/`
   - Shows "Check your email" message
   - For users who just registered

5. **VerifyEmailView** (View)
   - URL: `/accounts/verify-email/<token>/`
   - Verifies email via link click
   - Checks token expiry (24 hours)
   - Marks user as verified
   - Deletes used token

6. **VerifyEmailFormView** (FormView)
   - URL: `/accounts/verify-email/`
   - Manual token entry form
   - For users who prefer copy/paste
   - Validates token against database

7. **ResendVerificationView** (View)
   - URL: `/accounts/resend-verification/`
   - Deletes old tokens
   - Creates new token
   - Sends new email
   - POST only

#### **Password Reset Views:**

8. **ForgotPasswordView** (FormView)
   - URL: `/accounts/forgot-password/`
   - Accepts email address
   - Creates 1-hour reset token
   - Sends reset email
   - Doesn't reveal if email exists (security)

9. **ForgotPasswordDoneView** (TemplateView)
   - URL: `/accounts/forgot-password/done/`
   - Confirmation page

10. **ResetPasswordView** (FormView)
    - URL: `/accounts/reset-password/<token>/`
    - Validates token before showing form
    - Sets new password
    - Deletes used token
    - Redirects to login

#### **Profile Views:**

11. **ProfileView** (TemplateView)
    - URL: `/accounts/profile/`
    - Redirects to appropriate edit form
    - Personal → edit_personal_profile
    - Company → edit_company_profile

12. **EditPersonalProfileView** (UpdateView)
    - URL: `/accounts/profile/edit/personal/`
    - Edit job seeker profile
    - Personal accounts only
    - Auto-loads current user's profile
    - Shows success message

13. **EditCompanyProfileView** (UpdateView)
    - URL: `/accounts/profile/edit/company/`
    - Edit recruiter profile
    - Company accounts only
    - Auto-loads current user's profile
    - Shows success message

14. **PublicPersonalProfileView** (TemplateView)
    - URL: `/accounts/profile/<uuid>/personal/`
    - View someone's job seeker profile
    - Respects privacy settings
    - Shows 404 if profile not found

15. **PublicCompanyProfileView** (TemplateView)
    - URL: `/accounts/profile/<uuid>/company/`
    - View company profile
    - Always public (companies want visibility)
    - Shows company info and open jobs

---

### 4. **accounts_urls.py** → `apps/accounts/urls.py`
URL routing for all views.

**URL Patterns:**

```
/accounts/register/                           → RegisterView
/accounts/login/                              → LoginView
/accounts/logout/                             → LogoutView

/accounts/verify-email/notice/                → VerifyEmailNoticeView
/accounts/verify-email/<token>/               → VerifyEmailView (link click)
/accounts/verify-email/                       → VerifyEmailFormView (manual entry)
/accounts/resend-verification/                → ResendVerificationView

/accounts/forgot-password/                    → ForgotPasswordView
/accounts/forgot-password/done/               → ForgotPasswordDoneView
/accounts/reset-password/<token>/             → ResetPasswordView

/accounts/profile/                            → ProfileView (redirects)
/accounts/profile/edit/personal/              → EditPersonalProfileView
/accounts/profile/edit/company/               → EditCompanyProfileView

/accounts/profile/<uuid>/personal/            → PublicPersonalProfileView
/accounts/profile/<uuid>/company/             → PublicCompanyProfileView
```

---

## 🔧 Installation Steps

### **Step 1: Copy Files to Django App**

```bash
cd apps/accounts/

# Copy all files
cp /path/to/accounts_managers.py managers.py
cp /path/to/accounts_forms.py forms.py
cp /path/to/accounts_views.py views.py
cp /path/to/accounts_urls.py urls.py

# Also copy previous files
cp /path/to/accounts_models.py models.py
cp /path/to/accounts_admin.py admin.py
cp /path/to/accounts_signals.py signals.py
cp /path/to/accounts_decorators.py decorators.py
cp /path/to/accounts_apps.py apps.py
```

### **Step 2: Update models.py**

Make sure `models.py` imports the manager:

```python
# At the top of models.py
from .managers import UserManager

# In User model class
class User(AbstractBaseUser, PermissionsMixin):
    # ... fields ...
    
    objects = UserManager()  # Add this line
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
```

### **Step 3: Update Main URLs**

```python
# hiresight/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),  # Add this line
    # ... other paths
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### **Step 4: Update Settings**

```python
# hiresight/settings.py

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'apps.accounts',
]

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'dashboard:landing'

# Email settings (for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# For production, use SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
# DEFAULT_FROM_EMAIL = 'HireSight <noreply@hiresight.com>'
```

### **Step 5: Run Migrations**

```bash
python manage.py makemigrations accounts
python manage.py migrate accounts

# Create superuser
python manage.py createsuperuser
```

### **Step 6: Test in Shell**

```bash
python manage.py shell
```

```python
from apps.accounts.models import User

# Test user creation
user = User.objects.create_user(
    email='test@example.com',
    password='testpass123',
    account_type='personal'
)

print(user.email)  # test@example.com
print(user.account_type)  # personal
print(user.personal_profile.full_name)  # Test (auto-created)

# Test authentication
from django.contrib.auth import authenticate
auth_user = authenticate(username='test@example.com', password='testpass123')
print(auth_user)  # <User: test@example.com>
```

---

## 🎯 User Flows

### **Registration Flow:**

1. User visits `/accounts/register/`
2. Fills form (email, account type, password)
3. Submits form
4. Account created (is_verified=False)
5. Profile auto-created (Personal or Company)
6. Verification email sent with token
7. User redirected to `/accounts/verify-email/notice/`
8. User clicks link in email → `/accounts/verify-email/<token>/`
9. Email verified (is_verified=True)
10. User redirected to login

### **Login Flow:**

1. User visits `/accounts/login/`
2. Enters email & password
3. Checks "Remember me" (optional)
4. Submits form
5. Authenticated and logged in
6. Session set (2 weeks or browser close)
7. User redirected to dashboard

### **Password Reset Flow:**

1. User visits `/accounts/forgot-password/`
2. Enters email
3. Submits form
4. Reset email sent with 1-hour token
5. User redirected to "done" page
6. User clicks link in email → `/accounts/reset-password/<token>/`
7. Enters new password twice
8. Password updated
9. User redirected to login

### **Profile Edit Flow:**

1. User logs in
2. Visits `/accounts/profile/`
3. Redirected to edit form (personal or company)
4. Updates fields
5. Submits form
6. Profile saved
7. Success message shown
8. User stays on edit page

---

## 🔐 Security Features

### **Implemented:**
✅ Email-based authentication (no usernames)
✅ Password hashing (Django's built-in PBKDF2)
✅ CSRF protection (Django's built-in)
✅ Email verification required
✅ Token expiry (24h verification, 1h password reset)
✅ One-time use tokens (deleted after use)
✅ Case-insensitive email lookup
✅ Remember me with session expiry
✅ Profile privacy settings
✅ Login required decorators
✅ Role-based access decorators

### **To Add Later:**
- Rate limiting (Django Ratelimit)
- 2FA (django-two-factor-auth)
- Password strength requirements
- Account lockout after failed attempts
- IP-based security
- Audit logs

---

## 📧 Email Templates Needed

You'll need to create email templates for:

1. **Verification Email**
   - Subject: "Verify your HireSight email"
   - Body: Link to verify, expires in 24 hours

2. **Password Reset Email**
   - Subject: "Reset your HireSight password"
   - Body: Link to reset, expires in 1 hour

3. **Welcome Email** (optional)
   - Subject: "Welcome to HireSight!"
   - Body: Getting started guide

For now, emails use plain text. Later, create HTML templates with your branding.

---

## 🎨 HTML Templates Needed

You'll need to create these templates:

### **Authentication:**
1. `accounts/register.html` - Registration form
2. `accounts/login.html` - Login form
3. `accounts/verify_email_notice.html` - "Check your email" page
4. `accounts/verify_email.html` - Manual token entry form
5. `accounts/forgot_password.html` - Request reset form
6. `accounts/forgot_password_done.html` - "Email sent" page
7. `accounts/reset_password.html` - New password form

### **Profiles:**
8. `accounts/edit_personal_profile.html` - Edit job seeker profile
9. `accounts/edit_company_profile.html` - Edit recruiter profile
10. `accounts/public_personal_profile.html` - View job seeker profile
11. `accounts/public_company_profile.html` - View company profile

---

## ✅ Testing Checklist

### **Registration:**
- [ ] Register with personal account
- [ ] Register with company account
- [ ] Try duplicate email (should fail)
- [ ] Check verification email sent
- [ ] Click verification link
- [ ] Try expired verification link
- [ ] Resend verification email

### **Login:**
- [ ] Login with correct credentials
- [ ] Login with wrong password
- [ ] Login with non-existent email
- [ ] Test "remember me" checkbox
- [ ] Test logout

### **Password Reset:**
- [ ] Request password reset
- [ ] Click reset link
- [ ] Set new password
- [ ] Login with new password
- [ ] Try expired reset link

### **Profiles:**
- [ ] Edit personal profile
- [ ] Edit company profile
- [ ] Upload avatar/logo
- [ ] View public profile
- [ ] Test privacy settings

---

## 🚀 Next Steps

1. **Create HTML templates** with Tailwind CSS
2. **Test all flows** manually
3. **Add email templates** for better UX
4. **Add form validation** (client-side)
5. **Add profile photo cropping**
6. **Add social login** (Google, LinkedIn)

---

## 📝 Notes

- All views use class-based views for consistency
- All forms have Tailwind CSS pre-applied
- All URLs use named patterns (e.g., `accounts:login`)
- All views show user-friendly messages
- Email verification is required but not enforced yet
- Profile visibility is implemented but not enforced yet

**Ready for templates?** Let me know when you want me to create the HTML templates! 🎨