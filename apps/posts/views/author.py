from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions.base import IsAuthorOrAdmin
from apps.posts.models import Post, PostImage
from apps.posts.serializers import PostDetailSerializer, PostListSerializer, PostWriteSerializer


@extend_schema(tags=["Author Posts"])
class AuthorPostViewSet(ModelViewSet):
    permission_classes = [IsAuthorOrAdmin]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Post.objects.all().select_related("author", "category").prefetch_related("images")
        user = self.request.user
        return qs if user.is_superuser else qs.filter(author=user)

    def get_serializer_class(self):
        if self.action in ["retrieve"]:
            return PostDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return PostWriteSerializer
        return PostListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=["post"], detail=True, url_path="images", parser_classes=[MultiPartParser])
    def upload_image(self, request, slug=None):
        post = self.get_object()
        file = request.FILES.get("image")
        if not file:
            return Response({"detail": "No image provided."}, status=400)
        img = PostImage.objects.create(post=post, image=file)
        return Response({"id": img.pk, "url": img.image.url}, status=201)

    @action(methods=["get"], detail=False, url_path="mine")
    def my_posts(self, request):
        qs = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(qs)
        ser = PostListSerializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)
