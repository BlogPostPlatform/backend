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
        ]


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


class PostWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        read_only_fields = ["slug", "author", "published_at"]

        fields = [
            "title",
            "category",
            "short_description",
            "content",
            "cover_image",
            "status",
        ]
