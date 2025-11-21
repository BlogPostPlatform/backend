from django.core.exceptions import BadRequest
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.comments.models import Comment, CommentReaction
from apps.comments.pagination import CommentPageNumberPagination
from apps.comments.serializers import CommentCreateSerializer, CommentReadSerializer
from apps.posts.models import Post


@extend_schema(tags=["Posts"])
class CommentViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CommentPageNumberPagination
    filter_backends = [OrderingFilter]
    ordering = ["-created_at"]
    ordering_fields = ["likes", "dislikes", "created_at", "-created_at"]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return CommentCreateSerializer
        return CommentReadSerializer

    def get_queryset(self):
        post_slug = self.kwargs.get("post_slug")
        post = Post.objects.filter(slug=post_slug).first()
        if not post:
            return Comment.objects.none()

        self.total_comments = Comment.objects.filter(post__slug=post_slug).count()

        # Subquery for reply count (direct children only)
        reply_count_subquery = (
            Comment.objects.filter(parent=OuterRef("pk"))
            .values("parent")
            .annotate(count=Count("id"))
            .values("count")
        )

        # Subquery for likes
        likes_subquery = (
            CommentReaction.objects.filter(
                comment=OuterRef("pk"), reaction=CommentReaction.CommentReactionType.LIKE
            )
            .values("comment")
            .annotate(count=Count("id"))
            .values("count")
        )

        # Subquery for dislikes
        dislikes_subquery = (
            CommentReaction.objects.filter(
                comment=OuterRef("pk"), reaction=CommentReaction.CommentReactionType.DISLIKE
            )
            .values("comment")
            .annotate(count=Count("id"))
            .values("count")
        )

        return (
            Comment.objects.filter(post__slug=post_slug, parent__isnull=True)
            .select_related("author")
            .annotate(
                reply_count=Coalesce(Subquery(reply_count_subquery), 0),
                likes=Coalesce(Subquery(likes_subquery), 0),
                dislikes=Coalesce(Subquery(dislikes_subquery), 0),
            )
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["total_comments"] = self.total_comments
        return response

    def perform_create(self, serializer):
        post_slug = self.kwargs.get("post_slug")
        post = Post.objects.filter(slug=post_slug).first()
        serializer.save(author=self.request.user, post=post)

    def partial_update(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        comment = Comment.objects.filter(pk=pk).first()
        if comment.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You cannot edit this comment.")

        if not comment:
            raise BadRequest("Invalid comment id.")

        from apps.comments.models import CommentEditHistory

        CommentEditHistory.objects.create(comment=comment, previous_content=comment.content)

        comment.content = request.data.get("content", comment.content)
        comment.is_edited = True
        comment.save(update_fields=["content", "is_edited", "updated_at"])

        serializer = self.get_serializer(comment)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        comment = Comment.objects.filter(pk=pk).first()
        if comment.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You cannot delete this comment.")
        if not comment:
            raise BadRequest("Invalid comment id.")

        comment.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get"], detail=True, url_path="view-replies")
    def view_replies(self, request, post_slug=None, pk=None):
        comment = Comment.objects.filter(pk=pk).first()
        qs = Comment.objects.filter(parent=comment).annotate(
            likes=Count(
                "reactions",
                filter=Q(reactions__reaction=CommentReaction.CommentReactionType.LIKE),
                distinct=True,
            ),
            dislikes=Count(
                "reactions",
                filter=Q(reactions__reaction=CommentReaction.CommentReactionType.DISLIKE),
                distinct=True,
            ),
        )
        serializer = self.get_serializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @action(methods=["post"], detail=True, url_path="like")
    def like(self, request, post_slug=None, pk=None):
        pk = self.kwargs.get("pk")
        comment = Comment.objects.filter(pk=pk).first()

        if not comment:
            raise BadRequest("Invalid comment id.")

        reaction, created = CommentReaction.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={"reaction": CommentReaction.CommentReactionType.LIKE},
        )

        if not created:
            if reaction.reaction == CommentReaction.CommentReactionType.LIKE:
                reaction.delete()
            else:
                reaction.reaction = CommentReaction.CommentReactionType.LIKE
                reaction.save(update_fields=["reaction"])

        return Response({"success": True})

    @action(methods=["post"], detail=True, url_path="dislike")
    def dislike(self, request, post_slug=None, pk=None):
        pk = self.kwargs.get("pk")
        comment = Comment.objects.filter(pk=pk).first()

        if not comment:
            raise BadRequest("Invalid comment id.")

        reaction, created = CommentReaction.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={"reaction": CommentReaction.CommentReactionType.DISLIKE},
        )

        if not created:
            if reaction.reaction == CommentReaction.CommentReactionType.DISLIKE:
                reaction.delete()
            else:
                reaction.reaction = CommentReaction.CommentReactionType.DISLIKE
                reaction.save(update_fields=["reaction"])

        return Response({"success": True})
