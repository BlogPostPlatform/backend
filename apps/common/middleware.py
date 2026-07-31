import logging

from django.contrib.auth import get_user_model

from core.logging import is_health_check_path

logger = logging.getLogger(__name__)
User = get_user_model()


class HealthCheckLogFilterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._is_health_check = is_health_check_path(request.path)

        response = self.get_response(request)
        if request._is_health_check and response.status_code >= 400:
            logger.warning(
                "Health check failed: path=%s status=%s",
                request.path,
                response.status_code,
            )

        return response
