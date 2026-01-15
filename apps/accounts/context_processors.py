from django.utils import timezone
from django.conf import settings
from django.utils.translation import get_language
from .i18n_utils import get_all_languages, is_language_rtl, get_language_name


def unread_notifications_count(request):
    """Context processor to add unread notifications count to all templates."""
    if request.user.is_authenticated:
        try:
            # Get count of unread notifications
            count = request.user.notifications.filter(is_read=False).count()
        except AttributeError:
            # Handle case where notifications relationship doesn't exist yet
            count = 0
    else:
        count = 0

    return {
        'unread_notifications_count': count,
    }


def language_context(request):
    """Context processor to add language and i18n info to all templates."""
    current_language = get_language()
    
    return {
        'LANGUAGES': settings.LANGUAGES,
        'LANGUAGE_CODE': current_language,
        'LANGUAGE_NAME': get_language_name(current_language),
        'IS_RTL': is_language_rtl(current_language),
        'LANGUAGE_DIRECTION': 'rtl' if is_language_rtl(current_language) else 'ltr',
        'ALL_LANGUAGES': get_all_languages(),
    }
