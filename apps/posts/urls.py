from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthorPostViewSet, ClientPostViewSet

router = DefaultRouter()
router.register("author", AuthorPostViewSet, basename="author")
router.register("client", ClientPostViewSet, basename="client")

urlpatterns = [
    path("", include(router.urls)),
]
