"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django import setup

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
setup()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa
from django.core.asgi import get_asgi_application  # noqa

from apps.common.websocket_jwt_middleware import WebsocketJWTMiddleware  # noqa
from apps.notifications.routing import notification_urlpatterns  # noqa
from core.logging import install_daphne_health_check_access_log_filter  # noqa

install_daphne_health_check_access_log_filter()

urlpatterns = [*notification_urlpatterns]

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": WebsocketJWTMiddleware(URLRouter(urlpatterns)),
    }
)
