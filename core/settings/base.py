"""
Django base settings – shared across all environments.

Environment-specific modules (dev.py, test.py, prod.py) import
everything from here and override what they need.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

# ============================================================================
# Paths
# ============================================================================
# settings/ is one level deeper than the old settings.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

IN_K8S = "KUBERNETES_SERVICE_HOST" in os.environ

if IN_K8S:
    env_file = Path("/vault/secrets/backend.env")

    if not env_file.exists():
        raise ImproperlyConfigured(f"Vault secrets file does not exist: {env_file}")
    env.read_env(str(env_file))
else:
    env_file = BASE_DIR / ".env"

    if env_file.exists():
        env.read_env(str(env_file))
    elif (BASE_DIR / ".env.example").exists():
        env.read_env(str(BASE_DIR / ".env.example"))

if "DJANGO_ENV" not in os.environ:
    raise ImproperlyConfigured("DJANGO_ENV must be set explicitly in Kubernetes.")

# ============================================================================
# Core
# ============================================================================
SECRET_KEY = env.str("SECRET_KEY", default="")
DEBUG = False  # overridden per env
_explicit_settings_variant = os.environ.get("DJANGO_SETTINGS_MODULE", "").rpartition(".")[2]
DJANGO_ENV = (
    _explicit_settings_variant
    if _explicit_settings_variant in {"dev", "test", "prod"}
    else env.str("DJANGO_ENV", default="dev").lower()
)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

# ============================================================================
# Infrastructure hosts
# ============================================================================
REDIS_HOST = env.str("REDIS_HOST", default="127.0.0.1")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
REDIS_PASSWORD = env.str("REDIS_PASSWORD", "")

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
    "django.contrib.postgres",
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
    "apps.common.middleware.HealthCheckLogFilterMiddleware",
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
        "NAME": env.str("DATABASE_NAME", default="blog"),
        "USER": env.str("DATABASE_USER", default="postgres"),
        "PASSWORD": env.str("DATABASE_PASSWORD", default="postgres"),
        "HOST": env.str("DATABASE_HOST", default="localhost"),
        "PORT": env.int("DATABASE_PORT", default=5432),
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
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ============================================================================
# AWS / S3 – only used when USE_S3=True in .env
# ============================================================================
USE_S3 = env.bool("USE_S3", False)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if USE_S3:
    INSTALLED_APPS += ["storages"]

    AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
    AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL", default="")

    required = {
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
        "AWS_STORAGE_BUCKET_NAME": AWS_STORAGE_BUCKET_NAME,
        "AWS_S3_ENDPOINT_URL": AWS_S3_ENDPOINT_URL,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ImproperlyConfigured(f"USE_S3 is enabled but missing env vars: {missing}")

    AWS_S3_VERIFY = env.str("AWS_S3_VERIFY", "true").lower() in ("1", "true", "yes")
    AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default=True)
    AWS_QUERYSTRING_EXPIRE = env.int("AWS_QUERYSTRING_EXPIRE", default=3600)
    AWS_S3_USE_SSL = False
    AWS_DEFAULT_ACL = None

    # media -> S3
    STORAGES["default"] = {  # type: ignore
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "location": "media",
            "verify": AWS_S3_VERIFY,
            "querystring_auth": AWS_QUERYSTRING_AUTH,
            "querystring_expire": AWS_QUERYSTRING_EXPIRE,
        },
    }

# ============================================================================
# CORS / CSRF
# ============================================================================
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ],
)

# Canonical public frontend URL, used for links generated by background tasks.
# Additional browser origins belong in CORS_ALLOWED_ORIGINS, not numbered URL vars.
FRONTEND_URL = env.str("FRONTEND_URL", default="http://localhost:5173").rstrip("/")
if FRONTEND_URL not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

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
EMAIL_BACKEND = env.str("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env.str("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="email@example.com")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="password")
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)

# ============================================================================
# One-time passwords
# ============================================================================
OTP_LEN = env.int("OTP_LEN", default=6)
TTL_SECONDS = env.int("TTL_SECONDS", default=300)
MAX_ATTEMPTS = env.int("MAX_ATTEMPTS", default=5)

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
GOOGLE_OAUTH_CLIENT_ID = env.str("GOOGLE_OAUTH_CLIENT_ID", default="")

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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "suppress_successful_health_checks": {
            "()": "core.logging.SuccessfulHealthCheckAccessLogFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["suppress_successful_health_checks"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "django_server": {
            "level": "INFO",
            "filters": ["suppress_successful_health_checks"],
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.server": {
            "handlers": ["django_server"],
            "level": "INFO",
            "propagate": False,
        },
        "django.channels.server": {
            "handlers": ["django_server", "console"],
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
