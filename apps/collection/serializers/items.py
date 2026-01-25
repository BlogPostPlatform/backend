from rest_framework import serializers

from apps.collection.models import CollectionItem
from apps.posts.serializers import PostListSerializer


class CollectionItemReadSerializer(serializers.ModelSerializer):
    post = PostListSerializer()

    class Meta:
        model = CollectionItem
        fields = [
            "id",
            "collection",
            "post",
            "note",
            "position",
            "created_at",
            "updated_at",
        ]


class CollectionItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionItem
        fields = [
            "collection",
            "post_id",
            "note",
            "position",
            "created_at",
            "updated_at",
        ]

    def validate_note(self, value):
        if value is None:
            return value
        return value.strip()

    def validate(self, attrs):
        """
        Prevent duplicates within a collection (API level).
        DB constraint is still recommended.
        """
        collection = self.context.get("collection")
        post = attrs.get("post")

        if collection and post:
            exists = CollectionItem.objects.filter(collection=collection, post=post).exists()
            if exists and not getattr(self, "instance", None):
                raise serializers.ValidationError(
                    {"post_id": "This post is already in the collection."}
                )

        return attrs
