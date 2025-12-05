from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.permissions.base import IsAdmin, IsAuthorOrAdmin
from apps.posts.serializers import PostListSerializer
from apps.tags.models import Tag
from apps.tags.serializers import TagSerializer


@extend_schema(tags=["Tags"])
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().prefetch_related("posts")

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        elif self.action in ["create"]:
            return [IsAuthorOrAdmin()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == "posts":
            return PostListSerializer
        return TagSerializer

    @action(methods=["get"], detail=True, url_path="posts")
    def posts(self, request, pk=None):
        tag: Tag = self.get_object()
        qs = tag.posts.all().select_related("category", "author").prefetch_related("tags", "images")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
