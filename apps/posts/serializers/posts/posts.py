import datetime

from django.utils import timezone
from rest_framework import serializers

from apps.posts.models import Post


class PostListSerializer(serializers.ModelSerializer):
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

        if published_at and published_at < timezone.now():
            raise serializers.ValidationError(
                "Scheduled time to publish posts can't be in the past"
            )

        return attrs
