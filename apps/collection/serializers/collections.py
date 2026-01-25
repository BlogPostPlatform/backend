from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from apps.collection.models import Collection
from apps.users.serializers import PublicUserSerializer


class CollectionBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "name", "slug"]


class CollectionListSerializer(CollectionBaseSerializer):
    pass


class CollectionDetailSerializer(CollectionBaseSerializer):
    owner = PublicUserSerializer()
    items_count = serializers.IntegerField(read_only=True)

    class Meta(CollectionBaseSerializer.Meta):
        fields = CollectionBaseSerializer.Meta.fields + [
            "owner",
            "visibility",
            "description",
            "is_default",
            "items_count",
            "created_at",
            "updated_at",
        ]


class _CollectionWriteSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Collection
        fields = ["name", "slug", "visibility", "description", "is_default"]

    def validate_name(self, value):
        return value.strip()

    def validate(self, attrs):
        user = self.context["request"].user
        instance = getattr(self, "instance", None)

        name = attrs.get("name", instance.name if instance else None)
        slug = attrs.get("slug", instance.slug if instance else None)

        if not slug:
            slug = slugify(name)
            attrs["slug"] = slug

        qs = Collection.objects.filter(owner=user)
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if name and qs.filter(name__iexact=name).exists():
            raise serializers.ValidationError(
                {"name": "You already have a collection with this name."}
            )

        if slug and qs.filter(slug=slug).exists():
            raise serializers.ValidationError(
                {"slug": "You already have a collection with this slug."}
            )

        return attrs

    @transaction.atomic
    def _enforce_single_default(self, obj: Collection):
        if obj.is_default:
            Collection.objects.filter(owner=obj.owner).exclude(pk=obj.pk).update(is_default=False)


class CollectionCreateSerializer(_CollectionWriteSerializer):
    def create(self, validated_data):
        collection = super().create(validated_data)
        self._enforce_single_default(collection)
        return collection


class CollectionUpdateSerializer(_CollectionWriteSerializer):
    def update(self, instance, validated_data):
        collection = super().update(instance, validated_data)
        self._enforce_single_default(collection)
        return collection
