"""
Test settings – optimised for fast pytest runs.

Uses SQLite in-memory, disables throttling, uses eager Celery,
fast password hashing, and in-memory channel layer.
"""

import copy

from .base import *  # noqa: F401,F403

# ============================================================================
# Core
# ============================================================================
DEBUG = False

SECRET_KEY = "test-secret-key-not-for-production"  # noqa: S105

# ============================================================================
# Database – fast in-memory SQLite
# ============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# ============================================================================
# Password hashing – speed up test user creation
# ============================================================================
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ============================================================================
# Django REST Framework – no throttling during tests
# ============================================================================
REST_FRAMEWORK = copy.deepcopy(REST_FRAMEWORK)  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

# ============================================================================
# Simple JWT – short-lived tokens for tests
# ============================================================================
SIMPLE_JWT = copy.deepcopy(SIMPLE_JWT)  # noqa: F405
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=5)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(minutes=10)  # noqa: F405

# ============================================================================
# Email – capture everything in memory
# ============================================================================
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_HOST_USER = "test@example.com"

# ============================================================================
# Celery – run tasks synchronously
# ============================================================================
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ============================================================================
# Channels – in-memory layer (no Redis needed)
# ============================================================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ============================================================================
# Caches – local-memory cache (no Redis needed)
# ============================================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

# ============================================================================
# Storage – always use local filesystem in tests
# ============================================================================
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ============================================================================
# Logging – minimal, console only
# ============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "CRITICAL",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "CRITICAL",
    },
}

# ============================================================================
# Silk – disabled in tests
# ============================================================================
SILKY_IGNORE_PATHS = []

# ============================================================================
# Unfold admin
# ============================================================================
UNFOLD = copy.deepcopy(UNFOLD)  # noqa: F405
UNFOLD["ENVIRONMENT"] = "testing"
