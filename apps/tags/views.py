from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions.base import IsAdmin, IsAuthorOrAdmin
from apps.tags.models import Tag
from apps.tags.serializers import TagSerializer


@extend_schema(tags=["Tags"])
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().prefetch_related("posts")
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        elif self.action in ["create", "update", "partial_update"]:
            return [IsAuthorOrAdmin()]
        return [IsAdmin()]
