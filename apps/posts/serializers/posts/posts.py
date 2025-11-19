import datetime
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.posts.models import Post


class AuthorSerializer(serializers.Serializer):
    """Nested serializer for author info"""

    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "full_name": f"{instance.first_name} {instance.last_name}".strip() or instance.email,
            "email": instance.email,
        }


class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "cover_image",
            "created_at",
            "updated_at",
            "author",
            "published_at",
            "status",
        ]

    def get_cover_image(self, obj: Post):
        if obj.cover_image:
            context = self.context or {}
            request = context.get("request")
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class PostDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "short_description",
            "content",
            "cover_image",
            "author",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_cover_image(self, obj: Post):
        if obj.cover_image:
            context = self.context or {}
            request = context.get("request")
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        read_only_fields = ["author"]

        fields = [
            "title",
            "category",
            "slug",
            "short_description",
            "content",
            "cover_image",
            "status",
            "published_at",
        ]

    def validate(self, attrs):
        status = attrs.get("status")
        published_at: datetime.datetime | None = attrs.get("published_at", None)

        if status == "scheduled" and not published_at:
            raise serializers.ValidationError("You must specify a published at for scheduled posts")
        if published_at and published_at + timedelta(minutes=5) < timezone.now():
            raise serializers.ValidationError(
                "Scheduled time to publish posts can't be in the past"
            )
        return attrs
