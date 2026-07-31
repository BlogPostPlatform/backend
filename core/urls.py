"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Import admin customizations
import core.admin  # noqa

from .health import (
    liveness_probe,
    readiness_probe,
    startup_probe,
)

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("health/live/", liveness_probe),
    path("health/ready/", readiness_probe),
    path("health/startup/", startup_probe),
]

urlpatterns += [
    path("api/", include("apps.urls")),
]

if "drf_spectacular" in settings.INSTALLED_APPS and settings.DEBUG:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("api/schema/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/docs/", SpectacularAPIView.as_view(), name="schema"),
    ]

if "silk" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("api/silk/", include("silk.urls", namespace="silk")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
