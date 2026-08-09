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
        with connections["default"].cursor():
            pass
        checks["database"] = "ok"
    except OperationalError:
        checks["database"] = "failed"

    # ---------------------
    # Redis
    # ---------------------

    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
        )
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "failed"

    is_ready = all(check == "ok" for check in checks.values())

    return JsonResponse(
        {
            "status": "ready" if is_ready else "not_ready",
            "checks": checks,
        },
        status=200 if is_ready else 503,
    )
