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
            "allow_comments",
            "read_time",
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
    allowed_reactions = serializers.ListField(
        child=serializers.IntegerField(min_value=1), write_only=True, required=False
    )
    tags = serializers.ListField(
        child=serializers.IntegerField(min_value=1), write_only=True, required=False
    )

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
            "allow_comments",
        ]

    def validate(self, attrs):
        status = attrs.get("status")
        published_at = attrs.get("published_at", None)

        if status == "scheduled" and not published_at:
            raise serializers.ValidationError("You must specify a published at for scheduled posts")
        if published_at and published_at + timedelta(minutes=5) < timezone.now():
            raise serializers.ValidationError(
                "Scheduled time to publish posts can't be in the past"
            )

        # Validate allowed_reactions existence in ONE query
        allowed = attrs.get("allowed_reactions")
        if allowed:
            allowed_ids = list(dict.fromkeys(int(i) for i in allowed))  # dedupe & ints
            found = set(
                ReactionType.objects.filter(pk__in=allowed_ids).values_list("pk", flat=True)
            )
            missing = set(allowed_ids) - found
            if missing:
                raise serializers.ValidationError(
                    {"allowed_reactions": f"Not found: {sorted(missing)}"}
                )
            attrs["allowed_reactions"] = allowed_ids  # normalize to ints

        # Same for tags
        tags = attrs.get("tags")
        if tags:
            tag_ids = list(dict.fromkeys(int(i) for i in tags))
            found = set(Tag.objects.filter(pk__in=tag_ids).values_list("pk", flat=True))
            missing = set(tag_ids) - found
            if missing:
                raise serializers.ValidationError({"tags": f"Not found: {sorted(missing)}"})
            attrs["tags"] = tag_ids

        return attrs

    def create(self, validated_data):
        allowed_reactions = validated_data.pop("allowed_reactions", None)
        tags = validated_data.pop("tags", None)

        with transaction.atomic():
            instance = Post.objects.create(**validated_data)

            # Passing IDs to set() triggers Django's optimized path
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

        # IMPORTANT: only change m2m if client provided them
        if allowed_reactions is not None:
            instance.allowed_reactions.set(allowed_reactions)

        if tags is not None:
            instance.tags.set(tags)

        return instance
