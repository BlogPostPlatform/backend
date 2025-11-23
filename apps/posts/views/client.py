from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.bookmarks.models import Bookmark
from apps.common.pagination import PostPageNumberPagination
from apps.favourites.models import Favourite
from apps.posts.models import Post, Reaction, ReactionType
from apps.posts.serializers import (
    PostDetailSerializer,
    PostListSerializer,
    PostReactionsSerializer,
    ReactionPutSerializer,
)
from apps.users.models.user import Role, User


@extend_schema(tags=["Posts"])
class ClientPostViewSet(ReadOnlyModelViewSet):
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category__name"]
    search_fields = ["title", "short_description"]
    ordering_fields = ["published_at", "created_at"]
    pagination_class = PostPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        base = (
            Post.objects.select_related("author", "category")
            .prefetch_related("images", "allowed_reactions")
            .order_by("-published_at")
        )

        if user.is_anonymous:
            return base.filter(status=Post.Status.PUBLISHED)

        if user.role == Role.ADMIN:
            return base

        elif user.role == Role.AUTHOR:
            return base.filter(Q(author=user) | Q(status=Post.Status.PUBLISHED))

        return base.filter(status=Post.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        elif self.action == "put_reaction":
            return ReactionPutSerializer
        elif self.action in ["list_reactions", "remove_reaction"]:
            return PostReactionsSerializer
        return PostListSerializer

    def get_permissions(self):
        if self.action in ["favourite", "bookmark", "put_reaction"]:
            return [IsAuthenticated()]
        return [AllowAny()]

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
            .exclude(slug=post.slug)
            .select_related("author", "category")
            .order_by("-published_at")[:3]
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(methods=["post"], detail=True)
    def favourite(self, request, slug=None):
        post: Post = self.get_object()
        user = request.user

        Favourite.objects.get_or_create(user=user, post=post)
        return Response({"detail": "Post favorited."}, status=status.HTTP_201_CREATED)

    @favourite.mapping.delete
    def remove_favourite(self, request, slug=None):
        post: Post = self.get_object()
        user = request.user

        Favourite.objects.filter(user=user, post=post).delete()
        return Response({"detail": "Favourite removed."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def bookmark(self, request, slug=None):
        post = self.get_object()
        Bookmark.objects.get_or_create(user=request.user, post=post)
        return Response({"detail": "Bookmarked"}, status=201)

    @bookmark.mapping.delete
    def remove_bookmark(self, request, slug=None):
        post = self.get_object()
        Bookmark.objects.filter(user=request.user, post=post).delete()
        return Response(status=204)

    @action(methods=["post"], detail=True, url_path="put-reaction")
    def put_reaction(self, request, slug=None):
        post: Post = self.get_object()
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "post": post}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Get allowed reactions for this post
        if post.allowed_reactions.exists():
            qs = post.allowed_reactions.all()
        else:
            qs = ReactionType.objects.all()

        qs = qs.annotate(count=Count("reactions", filter=Q(reactions__post=post))).order_by("id")

        # Prefetch user's reactions once to avoid N+1
        user_reaction_ids = set()
        if request.user.is_authenticated:
            user_reaction_ids = set(
                Reaction.objects.filter(user=request.user, post=post).values_list(
                    "type_id", flat=True
                )
            )

        out = PostReactionsSerializer(
            qs,
            many=True,
            context={"request": request, "post": post, "user_reactions": user_reaction_ids},
        )
        return Response(out.data, status=status.HTTP_201_CREATED)

    @put_reaction.mapping.delete
    def remove_reaction(self, request, slug=None):
        post = self.get_object()
        Reaction.objects.filter(user=request.user, post=post).delete()

        # Get allowed reactions for this post
        if post.allowed_reactions.exists():
            qs = post.allowed_reactions.all()
        else:
            qs = ReactionType.objects.all()

        qs = qs.annotate(count=Count("reactions", filter=Q(reactions__post=post))).order_by("id")

        # No user reactions after deletion
        serializer = self.get_serializer(
            qs, many=True, context={"request": request, "post": post, "user_reactions": set()}
        )
        return Response(serializer.data)

    @action(methods=["get"], detail=True, url_path="list-reactions")
    def list_reactions(self, request, slug=None):
        post: Post = self.get_object()

        # Get allowed reactions for this post
        if post.allowed_reactions.exists():
            qs = post.allowed_reactions.all()
        else:
            # If no specific reactions are set, all are allowed
            qs = ReactionType.objects.none()

        qs = qs.annotate(count=Count("reactions", filter=Q(reactions__post=post))).order_by("id")

        # Prefetch user's reactions once to avoid N+1
        user_reaction_ids = set()
        if request.user.is_authenticated:
            user_reaction_ids = set(
                Reaction.objects.filter(user=request.user, post=post).values_list(
                    "type_id", flat=True
                )
            )

        serializer = self.get_serializer(
            qs,
            many=True,
            context={"request": request, "post": post, "user_reactions": user_reaction_ids},
        )
        return Response(serializer.data)
