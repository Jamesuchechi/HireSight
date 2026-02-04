
from pathlib import Path
import os
from decouple import config
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Application definition

INSTALLED_APPS = [
    'daphne',  # Django Channels ASGI server (must be first)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'axes',
    'csp',
    'django_ratelimit',
    'channels',  # Django Channels for WebSocket support
    'apps.accounts',
    'apps.resumes',
    'apps.jobs',
    'apps.applications',
    'apps.screening',
    'apps.dashboard',
    'apps.notifications',
    'apps.messaging',
    'apps.following',
    'apps.analytics',
    'apps.assessments',
    'apps.interviews',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.accounts.i18n_utils.LanguageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware', 
    'apps.accounts.middleware.SessionTrackingMiddleware', 
    'apps.accounts.middleware.CleanupExpiredSessionsMiddleware', 
    'apps.notifications.middleware.NotificationMiddleware',
    'apps.following.middleware.FollowCountMiddleware',
    'apps.accounts.middleware.EmailVerificationMiddleware',
    'apps.analytics.middleware.AnalyticsTrackingMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

ROOT_URLCONF = 'hiresight.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.accounts.context_processors.unread_notifications_count',
                'apps.accounts.context_processors.language_context',
                'apps.messaging.context_processors.unread_messages_count',
                'apps.notifications.context_processors.notification_dropdown_context',
                'apps.interviews.context_processors.interview_navigation_context',
            ],
            'builtins': ['apps.screening.templatetags.filters'],
        },
    },
]

WSGI_APPLICATION = 'hiresight.wsgi.application'



# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/howto/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
    ('fr', 'Français'),
    ('de', 'Deutsch'),
    ('it', 'Italiano'),
    ('pt', 'Português'),
    ('ja', '日本語'),
    ('zh', '中文'),
    ('ar', 'العربية'),
    ('hi', 'हिन्दी'),
    ('ru', 'Русский'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

QUESTION_POOL_COUNT_CACHE_TIMEOUT = 600  # seconds
ASSESSMENT_GENERATION_COOLDOWN_SECONDS = 300  # seconds

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Content Security Policy
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': (
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "'wasm-unsafe-eval'",
            "https://cdn.tailwindcss.com",
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://storage.googleapis.com",
        ),
        'style-src': (
            "'self'",
            "'unsafe-inline'",
            "https://cdn.tailwindcss.com",
            "https://fonts.googleapis.com",
        ),
        'font-src': (
            "'self'",
            "https://fonts.gstatic.com",
        ),
        'img-src': (
            "'self'",
            "data:",
            "blob:",
            "https:",
        ),
        'media-src': (
            "'self'",
            "blob:",
        ),
        'connect-src': (
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://storage.googleapis.com",
        ),
        'worker-src': (
            "'self'",
            "blob:",
        ),
    }
}


# Authentication backends
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Django Axes (Account Lockout)
AXES_FAILURE_LIMIT = 5  # Number of login attempts before lockout
AXES_COOLOFF_TIME = 1  # Hours to wait after lockout
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']

# Cache configuration for django-ratelimit
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
    }
}

# Rate Limiting
RATELIMIT_VIEW = 'accounts.views.ratelimit_view'

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/2')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'default'


CELERY_BEAT_SCHEDULE = {
    # Application Tasks
    'update-application-analytics': {
        'task': 'apps.applications.tasks.update_application_analytics',
        'schedule': crontab(hour=0, minute=0),
    },
    'cleanup-old-applications': {
        'task': 'apps.applications.tasks.cleanup_old_applications',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
    },
    
    # Screening Tasks
    'cleanup-old-screening-files': {
        'task': 'apps.screening.tasks.cleanup_old_screening_files',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
    },
    
    # Analytics Tasks
    'analytics-weekly-report': {
        'task': 'apps.analytics.tasks.send_weekly_analytics_report',
        'schedule': crontab(day_of_week='mon', hour=9, minute=0),
    },
    'analytics-monthly-report': {
        'task': 'apps.analytics.tasks.send_monthly_analytics_report',
        'schedule': crontab(day_of_month='1', hour=9, minute=0),
    },
    'predictive-analytics-snapshot': {
        'task': 'apps.analytics.tasks.generate_predictive_snapshots',
        'schedule': crontab(day_of_week='mon', hour=4, minute=0),
    },
    'salary-insights': {
        'task': 'apps.analytics.tasks.generate_salary_insights',
        'schedule': crontab(hour=5, minute=0),
    },
    'interview-questions': {
        'task': 'apps.analytics.tasks.generate_interview_questions',
        'schedule': crontab(day_of_week='mon', hour=2, minute=30),
    },
    'culture-fit-assessments': {
        'task': 'apps.analytics.tasks.assess_culture_fit',
        'schedule': crontab(day_of_week='tue', hour=3, minute=0),
    },
    'diversity-snapshots': {
        'task': 'apps.analytics.tasks.generate_diversity_snapshots',
        'schedule': crontab(day_of_week='wed', hour=3, minute=30),
    },
    'reference-checks': {
        'task': 'apps.analytics.tasks.kickoff_reference_checks',
        'schedule': crontab(day_of_week='thu', hour=4, minute=0),
    },
    
    # Assessment Tasks
    'cleanup-expired-attempts': {
        'task': 'apps.assessments.tasks.cleanup_expired_attempts',
        'schedule': crontab(hour='*/2'),  # Every 2 hours
    },
    'send-test-recommendations': {
        'task': 'apps.assessments.tasks.send_test_recommendation_emails',
        'schedule': crontab(day_of_week='mon', hour=9, minute=0), 
    },
    'send-test-reminders': {
        'task': 'apps.assessments.tasks.send_test_reminder_emails',
        'schedule': crontab(minute='0', hour='*/1'),
    },
    
    # Interview Tasks
    'send-interview-reminders': {
        'task': 'apps.interviews.tasks.send_interview_reminders',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-old-interviews': {
        'task': 'apps.interviews.tasks.cleanup_old_interviews',
        'schedule': crontab(day_of_month='1', hour=2, minute=0),  # 1st of month at 2 AM
    },
}

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'apps.accounts.validators.ComplexPasswordValidator',
    },
]

# Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@hiresight.com')
SITE_URL = config('SITE_URL', default='http://localhost:8000')

ADMIN_CONTACTS = config('ADMIN_CONTACTS', default='')
ADMINS = tuple(
    tuple(contact.split(':', 1))
    for contact in ADMIN_CONTACTS.split(',')
    if ':' in contact and contact.strip()
)
MANAGERS = ADMINS

# Mistral API Settings
MISTRAL_AI_API_KEY = config('MISTRAL_AI_API_KEY', default='')
MISTRAL_AI_BASE_URL = config('MISTRAL_AI_BASE_URL', default='https://api.mistral.ai/v1')
MISTRAL_AI_MODEL = config('MISTRAL_AI_MODEL', default='mistral-small-latest')
MISTRAL_AI_TIMEOUT = config('MISTRAL_AI_TIMEOUT', default=30, cast=int)

GROQ_API_KEY = config('GROQ_API_KEY', default='')
GROQ_API_URL = config('GROQ_API_URL', default='https://api.groq.com/openai/v1')
GROQ_MODEL = config('GROQ_MODEL', default='llama-3.3-70b-versatile')
GROQ_TIMEOUT = config('GROQ_TIMEOUT', default=30, cast=int)


# Session Settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Login Settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Admin Settings
ADMIN_URL = config('ADMIN_URL', default='admin/')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/security.log',
            'formatter': 'verbose',
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/celery.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'axes': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['celery_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps.interviews': {
            'handlers': ['file', 'celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Django Channels Configuration
# WebSocket and real-time updates support

ASGI_APPLICATION = 'hiresight.asgi_channels.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# For production, use Redis:
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             'hosts': [('127.0.0.1', 6379)],
#         },
#     },
# }

# WebSocket settings
WS_ALLOWED_ORIGINS = config(
    'WS_ALLOWED_ORIGINS',
    default='localhost:8000,127.0.0.1:8000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
# ==================== PRIVACY & SECURITY SETTINGS ====================

# Video retention policy
PRACTICE_VIDEO_RETENTION_DAYS = int(os.environ.get('PRACTICE_VIDEO_RETENTION_DAYS', 30))

# Rate limiting for practice sessions
PRACTICE_SESSIONS_PER_DAY_LIMIT = int(os.environ.get('PRACTICE_SESSIONS_PER_DAY_LIMIT', 5))

# AI model pricing (per 1K tokens)
AI_MODEL_PRICING = {
    'groq': 0.00015,      # $0.00015 per 1K tokens
    'mistral': 0.0002,    # $0.0002 per 1K tokens
    'openai': 0.0015,     # $0.0015 per 1K tokens
}

# Consent expiration (in days, None = never expires)
CONSENT_EXPIRATION_DAYS = int(os.environ.get('CONSENT_EXPIRATION_DAYS', 365))

# Video URL signing
VIDEO_SIGNED_URL_EXPIRATION_SECONDS = int(os.environ.get('VIDEO_SIGNED_URL_EXPIRATION_SECONDS', 900))  # 15 minutes

# Paths that require consent before access
CONSENT_REQUIRED_PATHS = [
    '/interviews/practice/',
]

# Paths exempted from consent requirement
CONSENT_EXEMPT_PATHS = [
    '/interviews/consent/',
    '/accounts/',
    '/api/auth/',
    '/static/',
    '/media/',
]
