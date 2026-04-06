"""
Language and localization utilities for HireSight.
"""
from django.conf import settings
from django.utils.translation import activate, get_language
from django.http import HttpResponseRedirect
from django.urls import reverse


class LanguageMiddleware:
    """Middleware to handle language preferences."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get language from various sources in order of priority
        language = None

        # 1. Check URL parameter
        if 'lang' in request.GET:
            language = request.GET.get('lang')

        # 2. Check session
        if not language and 'django_language' in request.session:
            language = request.session['django_language']

        # 3. Check cookie
        if not language:
            from django.utils.translation import get_language_from_request
            language = get_language_from_request(request)

        # 4. Check user preference (if authenticated)
        if not language and request.user.is_authenticated:
            try:
                user_language = getattr(request.user, 'preferred_language', None)
                if user_language:
                    language = user_language
            except AttributeError:
                pass

        # 5. Fallback to default
        if not language:
            language = settings.LANGUAGE_CODE

        # Validate language
        valid_languages = [code for code, _ in settings.LANGUAGES]
        if language not in valid_languages:
            language = settings.LANGUAGE_CODE

        # Activate language
        activate(language)
        request.LANGUAGE_CODE = language

        # Store in session
        request.session['django_language'] = language

        response = self.get_response(request)

        # Set language cookie
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
        )

        return response


def get_rtl_languages():
    """Get list of RTL (right-to-left) languages."""
    return ['ar', 'he']


def is_language_rtl(language_code):
    """Check if language is RTL."""
    return language_code in get_rtl_languages()


def get_language_name(language_code):
    """Get display name for language code."""
    for code, name in settings.LANGUAGES:
        if code == language_code:
            return name
    return language_code


def get_all_languages():
    """Get all available languages."""
    return [
        {
            'code': code,
            'name': name,
            'is_rtl': is_language_rtl(code),
        }
        for code, name in settings.LANGUAGES
    ]


def get_active_language_info():
    """Get info about active language."""
    language_code = get_language()
    return {
        'code': language_code,
        'name': get_language_name(language_code),
        'is_rtl': is_language_rtl(language_code),
    }


def translate_choice_field(choices):
    """Translate choice field options.
    
    Usage in models:
        from django.utils.translation import gettext_lazy as _
        STATUS_CHOICES = [
            ('pending', _('Pending')),
            ('approved', _('Approved')),
        ]
    """
    return [(code, str(label)) for code, label in choices]


def get_language_direction():
    """Get text direction for current language."""
    return 'rtl' if is_language_rtl(get_language()) else 'ltr'
