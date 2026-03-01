"""
Django base settings – shared across all environments.

Environment-specific modules (dev.py, test.py, prod.py) import
everything from here and override what they need.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

# ============================================================================
# Paths
# ============================================================================
# settings/ is one level deeper than the old settings.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ============================================================================
# Core
# ============================================================================
SECRET_KEY = config("SECRET_KEY", default="")
DEBUG = False  # overridden per env

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

# ============================================================================
# Infrastructure hosts
# ============================================================================
REDIS_HOST = config("REDIS_HOST", default="127.0.0.1")
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)

# ============================================================================
# Application definition
# ============================================================================
DJANGO_APPS = [
    "daphne",
    "unfold",
    "unfold.contrib.forms",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "channels",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_celery_beat",
    "django_filters",
    "django_cleanup.apps.CleanupConfig",
    "storages",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.analytics",
    "apps.bookmarks",
    "apps.categories",
    "apps.collection",
    "apps.comments",
    "apps.common",
    "apps.favourites",
    "apps.logs",
    "apps.notifications",
    "apps.posts",
    "apps.tags",
    "apps.users",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================================================
# Middleware
# ============================================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ============================================================================
# URL / Template / ASGI
# ============================================================================
ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "core.asgi.application"

# ============================================================================
# Database
# ============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="blog"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# ============================================================================
# Password validation
# ============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ============================================================================
# i18n / l10n
# ============================================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [
    ("en", "English"),
    ("uz", "Uzbek"),
    ("ru", "Russian"),
]

# ============================================================================
# Static & Media files
# ============================================================================
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ============================================================================
# AWS / S3 – only used when USE_S3=True in .env
# ============================================================================
USE_S3 = config("USE_S3", default=False, cast=bool)

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="")
AWS_PUBLIC_BUCKET_NAME = config("AWS_PUBLIC_BUCKET_NAME", default="")
AWS_PRIVATE_BUCKET_NAME = config("AWS_PRIVATE_BUCKET_NAME", default="")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False

if USE_S3:
    STORAGES = {
        "default": {
            "BACKEND": "core.storages.PublicMediaStorage",
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
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# ============================================================================
# CORS / CSRF
# ============================================================================
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080",  # noqa
    cast=Csv(),
)

# Append extra origins from env vars (backwards-compat)
_extra_origins = [
    config("FRONTEND_URL", default=""),
    config("FRONTEND_URL_1", default=""),
    config("FRONTEND_URL_2", default=""),
]
CORS_ALLOWED_ORIGINS += [o for o in _extra_origins if o]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "accept-language",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============================================================================
# Django REST Framework – conservative defaults (overridden per env)
# ============================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/min",
        "user": "1000/min",
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ============================================================================
# Simple JWT – conservative defaults (overridden per env)
# ============================================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": (
        "rest_framework_simplejwt.authentication.default_user_authentication_rule"
    ),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# ============================================================================
# Email
# ============================================================================
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="email@example.com")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="password")

# ============================================================================
# Celery
# ============================================================================
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "Asia/Tashkent"
CELERY_ENABLE_UTC = False
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 1800
CELERY_TASK_SOFT_TIME_LIMIT = 1200
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_DEFAULT_QUEUE = "celery"
CELERY_TASK_CREATE_MISSING_QUEUES = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_LOG_COLOR = True
CELERYD_HIJACK_ROOT_LOGGER = False
CELERYD_LOG_COLOR = False
CELERY_TASK_SEND_SENT_EVENT = False

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {}

# ============================================================================
# Cache
# ============================================================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

# ============================================================================
# Channels
# ============================================================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, int(REDIS_PORT))],
        },
    },
}

# ============================================================================
# Google OAuth
# ============================================================================
GOOGLE_OAUTH_CLIENT_ID = config("GOOGLE_OAUTH_CLIENT_ID", default="")

# ============================================================================
# DRF Spectacular
# ============================================================================
SPECTACULAR_SETTINGS = {
    "TITLE": "Blog Website API",
    "DESCRIPTION": "Blog Website API",
    "VERSION": "1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
    "SECURITY": [{"BearerAuth": []}],
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
}

# ============================================================================
# Logging – base (no "db" handler; envs opt-in)
# ============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}:{lineno} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "app.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        # Silence noisy third-party loggers
        "celery": {"handlers": [], "level": "WARNING", "propagate": False},
        "celery.worker.strategy": {"handlers": [], "level": "WARNING", "propagate": False},
        "celery.app.trace": {"handlers": [], "level": "ERROR", "propagate": False},
        "celery.beat": {"handlers": [], "level": "WARNING", "propagate": False},
        "kombu": {"handlers": [], "level": "WARNING", "propagate": False},
        "amqp": {"handlers": [], "level": "WARNING", "propagate": False},
        "apps.posts.tasks": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ============================================================================
# Unfold Admin
# ============================================================================
from django.templatetags.static import static  # noqa: E402
from django.urls import reverse  # noqa: E402

UNFOLD = {
    "SITE_TITLE": "Blog Post Admin",
    "SITE_HEADER": "Blog Administration",
    "SITE_URL": lambda request: reverse("admin:index"),
    "SITE_ICON": lambda request: static("icon.png"),
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Content Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Posts",
                        "icon": "description",
                        "link": lambda request: reverse("admin:posts_post_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "folder",
                        "link": lambda request: reverse("admin:categories_category_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "sell",
                        "link": lambda request: reverse("admin:tags_tag_changelist"),
                    },
                ],
            },
            {
                "title": "User Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": lambda request: reverse("admin:users_user_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": lambda request: reverse("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": "System",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "View Site",
                        "icon": "language",
                        "link": lambda request: reverse("admin:index"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["posts.post"],
            "items": [
                {
                    "title": "All Posts",
                    "link": lambda request: reverse("admin:posts_post_changelist"),
                    "icon": "description",
                },
                {
                    "title": "Published",
                    "link": lambda request: reverse("admin:posts_post_changelist")
                    + "?status__exact=published",
                    "icon": "check_circle",
                },
                {
                    "title": "Drafts",
                    "link": lambda request: reverse("admin:posts_post_changelist")
                    + "?status__exact=draft",
                    "icon": "edit",
                },
            ],
        },
        {
            "models": ["tags.tag"],
            "items": [
                {
                    "title": "All Tags",
                    "link": lambda request: reverse("admin:tags_tag_changelist"),
                    "icon": "sell",
                },
            ],
        },
        {
            "models": ["users.user"],
            "items": [
                {
                    "title": "All Users",
                    "link": lambda request: reverse("admin:users_user_changelist"),
                    "icon": "people",
                },
                {
                    "title": "Active Users",
                    "link": lambda request: reverse("admin:users_user_changelist")
                    + "?is_active__exact=1",
                    "icon": "check_circle",
                },
                {
                    "title": "Verified",
                    "link": lambda request: reverse("admin:users_user_changelist")
                    + "?email_verified__exact=1",
                    "icon": "verified",
                },
            ],
        },
    ],
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇳🇱",
            },
        },
    },
    "ENVIRONMENT": "development",
    "LOGIN": {
        "redirect_after": lambda request: reverse("admin:index"),
    },
    "SHOW_LANGUAGES": False,
    "SHOW_VIEW_ON_SITE": True,
}
