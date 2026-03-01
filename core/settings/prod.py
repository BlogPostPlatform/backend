"""
Production settings.

Disables debug, swagger, silk, and DB log writes.
Enforces strict security headers and conservative rate limits.
"""

import copy

from .base import *  # noqa: F401,F403

# ============================================================================
# Core
# ============================================================================
DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())  # noqa: F405

# ============================================================================
# Installed apps – remove dev/debug tools
# ============================================================================
# silk is not in base INSTALLED_APPS, so nothing to remove
# drf_spectacular stays installed (migrations) but swagger URLs are guarded

# ============================================================================
# Django REST Framework – strict rates, no browsable API
# ============================================================================
REST_FRAMEWORK = copy.deepcopy(REST_FRAMEWORK)  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "60/min",
    "user": "300/min",
}

# ============================================================================
# Simple JWT – short-lived tokens for production
# ============================================================================
SIMPLE_JWT = copy.deepcopy(SIMPLE_JWT)  # noqa: F405
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=30)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=7)  # noqa: F405

# ============================================================================
# Security
# ============================================================================
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)  # noqa: F405
SECURE_HSTS_SECONDS = 31_536_000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ============================================================================
# Logging – NO database handler, file + console only
# ============================================================================
LOGGING = copy.deepcopy(LOGGING)  # noqa: F405
LOGGING["handlers"].pop("db", None)
# Ensure root handlers have no "db"
LOGGING["root"]["handlers"] = ["console", "file"]
for _logger_cfg in LOGGING["loggers"].values():
    if "db" in _logger_cfg.get("handlers", []):
        _logger_cfg["handlers"].remove("db")

# ============================================================================
# Silk – completely disabled
# ============================================================================
SILKY_IGNORE_PATHS = []

# ============================================================================
# Unfold admin
# ============================================================================
UNFOLD = copy.deepcopy(UNFOLD)  # noqa: F405
UNFOLD["ENVIRONMENT"] = "production"
