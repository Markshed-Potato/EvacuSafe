"""
Django settings for the EvacuSafe project (config package).
Vertical-slicing structure (apps/, static/, templates/) + Supabase (PostgreSQL) integration.
Hardened for production security, automated testing, and auditable disaster management.
"""

import sys
from pathlib import Path
from decouple import config, UndefinedValueError
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Detect test runner execution to isolate tests from production database
IS_TESTING = 'test' in sys.argv

# ---------------------------------------------------------------------------
# Core / Security Hardening
# ---------------------------------------------------------------------------
# Default DEBUG to False unless explicitly set to True in environment
DEBUG = config('DEBUG', default=False, cast=bool)

# Require SECRET_KEY from environment in production; allow dev/test fallback
if DEBUG or IS_TESTING:
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-secret-key-for-local-testing-and-dev')
else:
    try:
        SECRET_KEY = config('SECRET_KEY')
        if not SECRET_KEY or SECRET_KEY.startswith('django-insecure-change-me'):
            raise ValueError("Insecure or placeholder SECRET_KEY cannot be used in production.")
    except UndefinedValueError:
        raise ValueError("SECRET_KEY environment variable is strictly required when DEBUG=False.")

# Allowed hosts
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',') if h.strip()]

# CSRF Trusted Origins
csrf_trusted_raw = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:8080,http://localhost:8080'
)
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_raw.split(',') if origin.strip()]

# Production SSL & HTTP Security Headers
if not DEBUG and not IS_TESTING:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ---------------------------------------------------------------------------
# Applications (each app = one vertical slice, grouped under apps/)
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    # local apps (vertical slices, under apps/)
    'apps.login',
    'apps.register',
    'apps.home',
    'apps.profile',
    'apps.user_settings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------------------
# Database Configuration
# - Automated test runs (`manage.py test`) ALWAYS use isolated in-memory SQLite
# - Production/Dev connects to Supabase PostgreSQL via DATABASE_URL
# - Falls back to local SQLite if DATABASE_URL is blank or USE_SQLITE=True
# ---------------------------------------------------------------------------
DATABASE_URL = config('DATABASE_URL', default='').strip()
USE_SQLITE = config('USE_SQLITE', default=False, cast=bool)
IS_INACTIVE_TENANT = 'tbagvomzegfpexashzwf' in DATABASE_URL or '[YOUR-PROJECT-REF]' in DATABASE_URL

if IS_TESTING:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif USE_SQLITE or not DATABASE_URL or (DEBUG and IS_INACTIVE_TENANT):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    db_config = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=config('CONN_MAX_AGE', default=600, cast=int),
        ssl_require=config('DB_SSL_REQUIRE', default=True, cast=bool),
    )
    if config('DB_SSL_REQUIRE', default=True, cast=bool):
        options = db_config.setdefault('OPTIONS', {})
        if 'sslmode' not in options:
            options['sslmode'] = 'require'
    DATABASES = {'default': db_config}

# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalization & Localization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('fil', 'Filipino'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# ---------------------------------------------------------------------------
# Static & Media files (CSS, JavaScript, Images)
# WhiteNoise enables direct, production-grade static asset serving.
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

if IS_TESTING or DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Auth redirects
# ---------------------------------------------------------------------------
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# ---------------------------------------------------------------------------
# Email Backend Configuration (Alerts & Emergency Broadcasts)
# ---------------------------------------------------------------------------
if DEBUG or IS_TESTING:
    EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
else:
    EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='EvacuSafe Alerts <alerts@evacusafe.org>')

# ---------------------------------------------------------------------------
# Supabase & External Integrations
# ---------------------------------------------------------------------------
SUPABASE_URL = config('SUPABASE_URL', default='')
SUPABASE_ANON_KEY = config('SUPABASE_ANON_KEY', default='')
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')
