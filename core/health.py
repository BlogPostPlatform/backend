import redis
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse


def liveness_probe(request):
    """
    Is Django process alive?

    DO NOT check database.
    DO NOT check redis.
    DO NOT check camunda.
    """

    return JsonResponse(
        {"status": "alive"},
        status=200,
    )


def startup_probe(request):
    """
    Has Django fully started?

    If this endpoint responds, startup finished.
    """

    return JsonResponse(
        {"status": "started"},
        status=200,
    )


def readiness_probe(request):
    """
    Can this pod serve traffic?

    Check external dependencies here.
    """

    checks = {}

    # ---------------------
    # PostgreSQL
    # ---------------------

    try:
        connections["default"].cursor()
        checks["database"] = "ok"
    except OperationalError:
        checks["database"] = "failed"

    # ---------------------
    # Redis
    # ---------------------

    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "failed"
