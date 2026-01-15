# Authentication Templates

This folder contains all authentication-related templates for HireSight.

## Files

1. **login.html** - User sign in page
2. **register.html** - Account creation with Personal/Company selection
3. **verify_email_notice.html** - Post-registration email verification notice
4. **forgot_password.html** - Password reset request form
5. **forgot_password_done.html** - Confirmation after reset email sent
6. **reset_password.html** - Set new password form (with token)

## Installation

Copy these files to your Django project:

```bash
cp *.html /path/to/your/project/templates/accounts/
```

## Template Paths

Your views should reference:
- `accounts/login.html`
- `accounts/register.html`
- `accounts/verify_email_notice.html`
- `accounts/forgot_password.html`
- `accounts/forgot_password_done.html`
- `accounts/reset_password.html`

## Features

✅ Beautiful two-column layouts
✅ Responsive (mobile, tablet, desktop)
✅ Password visibility toggle
✅ Account type selector
✅ Social login buttons
✅ Form validation
✅ Flash message support
✅ Gradient backgrounds
✅ Smooth animations

## See Also

- **AUTH_TEMPLATES_GUIDE.md** - Complete documentation
- **base.html** - Main layout template (in parent directory)

🎉 Your Complete Authentication System is Ready!
I've created 7 production-ready templates with stunning design!
✨ What You Got:
📄 Templates (7 files):

base.html - Master template with:

Role-based navigation (Personal vs Company)
Notification dropdown with badge
User menu with avatar
Flash messages system
Footer
Mobile responsive menu


login.html - Sign in with:

Email & password
Password toggle
Remember me
Forgot password link
Social login buttons
Testimonial sidebar


register.html - Sign up with:

Beautiful account type selector (Personal/Company cards)
Email & passwords
Terms checkbox
Social signup
Benefits sidebar


verify_email_notice.html - After registration:

Email sent confirmation
Instructions
Resend button


forgot_password.html - Reset request:

Email field
Clear instructions


forgot_password_done.html - Reset confirmation:

Check email message
Next steps guide


reset_password.html - Set new password:

New password with toggle
Confirm password
Requirements checklist



📚 Documentation:

AUTH_TEMPLATES_GUIDE.md - Complete guide with:

Template details
Design features
Usage instructions
Testing checklist
Responsive breakpoints

🎨 Design Highlights:
✅ Two-column split layouts (form left, features right)
✅ White & blue color scheme (consistent with landing page)
✅ Password visibility toggles (Alpine.js powered)
✅ Beautiful account type selector (card-style radios)
✅ Gradient buttons with ripple effects
✅ Social login buttons (Google, LinkedIn ready)
✅ Responsive (mobile hides right column)
✅ Smooth animations everywhere
✅ Icon-rich interfaces (Heroicons)
✅ Flash messages (slide in, auto-dismiss)
🎯 Special Features:
1. Account Type Selector (Register):
Beautiful card-style radio buttons:

Job Seeker card (blue gradient)
Recruiter card (cyan gradient)
Icons and descriptions
Hover & selected states

2. Password Toggle:
Click eye icon to show/hide password:
<button @click="showPassword = !showPassword">
    <!-- Switches between eye and eye-slash icons -->
</button>

3. Flash Messages:
Automatic from Django:
messages.success(request, 'Logged in!')
messages.error(request, 'Invalid credentials')
```
Shows as beautiful toast in top-right corner!

## 📂 **File Structure:**
```
/mnt/user-data/outputs/
├── base.html                      # Master template
├── auth/                          # Auth templates folder
│   ├── README.md                  # Quick reference
│   ├── login.html
│   ├── register.html
│   ├── verify_email_notice.html
│   ├── forgot_password.html
│   ├── forgot_password_done.html
│   └── reset_password.html
└── AUTH_TEMPLATES_GUIDE.md        # Complete documentation

🚀 To Use These:
1. Copy to your Django project:

# Copy base template
cp base.html /your/project/templates/

# Copy auth templates
cp -r auth/* /your/project/templates/accounts/

2. Your views already reference correct paths:

# views.py (already configured)
template_name = 'accounts/login.html'
template_name = 'accounts/register.html'
# etc.

3. Forms already have Tailwind classes:

# forms.py (already configured with widget classes)
widget=forms.EmailInput(attrs={
    'class': 'w-full pl-12 pr-4 py-3 ...',
})



Register → Verify email → Login ✅
Login → Dashboard ✅
Forgot password → Reset → Login ✅