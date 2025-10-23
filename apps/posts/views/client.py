from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.common.pagination import PostPageNumberPagination
from apps.posts.models import Post
from apps.posts.serializers import PostDetailSerializer, PostListSerializer
from apps.users.models import User
from apps.users.models.user import Role


@extend_schema(tags=["Client Posts"])
class ClientPostViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category__name"]
    search_fields = ["title", "short_description"]
    ordering_fields = ["published_at", "created_at"]
    pagination_class = PostPageNumberPagination

    def paginate_queryset(self, queryset):
        if self.action == "list":
            return super().paginate_queryset(queryset)
        return None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        return (
            Post.published.select_related("author", "category")
            .prefetch_related("images")
            .order_by("-published_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostListSerializer

    @action(methods=["get"], detail=False, url_path="latest-posts")
    def latest_posts(self, request):
        queryset = self.get_queryset().filter()[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=False, url_path="trending-posts")
    def trending_posts(self, request):
        queryset = self.get_queryset().filter()[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=False, url_path="most-popular-posts")
    def most_popular_posts(self, request):
        queryset = self.get_queryset().filter()[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=False, url_path="homepage-statistics")
    def homepage_statistics(self, request):
        # serializer = self.get_serializer()
        articles = Post.objects.aggregate(
            articles=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        )["articles"]
        writers = User.objects.aggregate(
            writers=Count("id", filter=Q(role=Role.AUTHOR), distinct=True)
        )["writers"]
        return Response({"Active Readers": "50000", "Articles": articles, "Writers": writers})

    @action(methods=["get"], detail=True, url_path="related-posts")
    def related_posts(self, request, slug=None):
        post: Post = self.get_object()
        qs = (
            post.category.posts.all()
            .select_related("author", "category")
            .order_by("-published_at")[:5]
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
