import datetime
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.posts.models import Post, ReactionType
from apps.tags.models import Tag
from apps.tags.serializers import TagSerializer


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
    allowed_reactions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ReactionType.objects.all(), required=False
    )
    tags = TagSerializer(many=True, read_only=True)

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
            "allowed_reactions",
            "tags",
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
    allowed_reactions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ReactionType.objects.all(), required=False
    )
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

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
            "allowed_reactions",
            "tags",
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

        allowed_reactions = attrs.get("allowed_reactions", [])
        for reaction in allowed_reactions:
            if not ReactionType.objects.filter(pk=reaction.pk).exists():
                raise serializers.ValidationError("Reaction type does not exist")

        return attrs

    def create(self, validated_data):
        allowed_reactions = validated_data.pop("allowed_reactions", None)
        tags = validated_data.pop("tags", None)

        with transaction.atomic():
            instance = Post.objects.create(**validated_data)
            if allowed_reactions:
                instance.allowed_reactions.set(allowed_reactions)
            if tags:
                instance.tags.set(tags)
        return instance

    def update(self, instance: Post, validated_data):
        allowed_reactions = validated_data.pop("allowed_reactions", None)
        tags = validated_data.pop("tags", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        instance.allowed_reactions.clear()
        if allowed_reactions is not None:
            instance.allowed_reactions.set(allowed_reactions)

        if tags:
            instance.tags.set(tags)

        return instance
