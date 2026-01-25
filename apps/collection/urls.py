from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import CollectionItemViewSet, CollectionViewSet

router = DefaultRouter()
router.register(r"", CollectionViewSet, basename="collection")

collections_router = NestedDefaultRouter(router, r"", lookup="collection")
collections_router.register(r"items", CollectionItemViewSet, basename="collection-items")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(collections_router.urls)),
]
