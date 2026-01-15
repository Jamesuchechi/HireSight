"""
Views for language switching and i18n support.
"""
from django.shortcuts import redirect
from django.conf import settings
from django.utils.translation import activate
from django.views import View
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme


class SetLanguageView(View):
    """View to set user's preferred language."""

    def post(self, request, *args, **kwargs):
        """Set language preference."""
        try:
            language = request.POST.get('language', request.GET.get('language'))
            next_url = request.POST.get('next', request.GET.get('next', '/'))

            # Validate language
            valid_languages = [code for code, _ in settings.LANGUAGES]
            if language not in valid_languages:
                language = settings.LANGUAGE_CODE

            # Validate next URL
            if not url_has_allowed_host_and_scheme(next_url):
                next_url = '/'

            # Activate language
            activate(language)

            # Store in session
            request.session['django_language'] = language

            # Save to user profile if authenticated
            if request.user.is_authenticated:
                try:
                    user = request.user
                    user.preferred_language = language
                    user.save(update_fields=['preferred_language'])
                except AttributeError:
                    # User model doesn't have preferred_language field
                    pass

            # Create response
            response = redirect(next_url)

            # Set language cookie
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                language,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
            )

            return response

        except Exception as e:
            return redirect('/')


class LanguageAPIView(View):
    """API view for language operations."""

    def get(self, request, *args, **kwargs):
        """Get available languages and current language."""
        try:
            from apps.accounts.i18n_utils import get_all_languages, get_active_language_info

            return JsonResponse({
                'success': True,
                'current': get_active_language_info(),
                'available': get_all_languages(),
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def post(self, request, *args, **kwargs):
        """Set language via API."""
        try:
            import json
            data = json.loads(request.body)
            language = data.get('language')

            # Validate language
            valid_languages = [code for code, _ in settings.LANGUAGES]
            if language not in valid_languages:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid language: {language}'
                }, status=400)

            # Activate language
            activate(language)

            # Store in session
            request.session['django_language'] = language

            # Save to user profile if authenticated
            if request.user.is_authenticated:
                try:
                    user = request.user
                    user.preferred_language = language
                    user.save(update_fields=['preferred_language'])
                except AttributeError:
                    pass

            from apps.accounts.i18n_utils import get_active_language_info

            return JsonResponse({
                'success': True,
                'message': f'Language set to {language}',
                'language': get_active_language_info(),
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
