"""
Development settings.

Enables debug mode, silk profiler, browsable API, generous
throttle rates, and long-lived JWT tokens for local development.
"""

import copy

from .base import *  # noqa: F401,F403

# ============================================================================
# Core
# ============================================================================
DEBUG = True

ALLOWED_HOSTS = ["*"]

# ============================================================================
# Installed apps – add dev-only apps
# ============================================================================
INSTALLED_APPS = [*INSTALLED_APPS, "silk", "drf_spectacular"]  # noqa: F405

# ============================================================================
# Middleware – add silk profiler (new list to avoid mutating base)
# ============================================================================
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
_wn_idx = MIDDLEWARE.index("whitenoise.middleware.WhiteNoiseMiddleware")
MIDDLEWARE.insert(_wn_idx + 1, "silk.middleware.SilkyMiddleware")

# ============================================================================
# Django REST Framework
# ============================================================================
# The inherited throttle configuration is explicitly replaced immediately below.
REST_FRAMEWORK = copy.deepcopy(REST_FRAMEWORK)  # noqa: F405  # nosemgrep
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = (
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
    "rest_framework.throttling.ScopedRateThrottle",
)
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1500/min",
    "user": "30000/min",
}
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    *REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"],
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# ============================================================================
# Simple JWT – generous lifetimes for development
# ============================================================================
SIMPLE_JWT = copy.deepcopy(SIMPLE_JWT)  # noqa: F405
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(days=60)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=60)  # noqa: F405

# ============================================================================
# Silk profiler
# ============================================================================
SILKY_IGNORE_PATHS = [r"^static/", r"^media/"]
SILKY_PYTHON_PROFILER_BINARY = False
SILKY_WARNINGS = False

# ============================================================================
# Logging – add database handler for dev
# ============================================================================
LOGGING = copy.deepcopy(LOGGING)  # noqa: F405
LOGGING["handlers"]["db"] = {
    "level": "INFO",
    "class": "apps.logs.handlers.DatabaseHandler",
    "formatter": "verbose",
}
LOGGING["root"]["handlers"].append("db")
for _logger_name, _level in (("django.request", "ERROR"), ("apps.posts.tasks", "INFO")):
    _logger_config = LOGGING["loggers"].setdefault(
        _logger_name,
        {"handlers": ["console"], "level": _level, "propagate": False},
    )
    if "db" not in _logger_config["handlers"]:
        _logger_config["handlers"].append("db")

# ============================================================================
# Unfold admin
# ============================================================================
UNFOLD = copy.deepcopy(UNFOLD)  # noqa: F405
UNFOLD["ENVIRONMENT"] = "development"
