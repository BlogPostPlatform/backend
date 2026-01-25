from django.db import transaction
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import (
    mixins,
    serializers,
    viewsets,
)
from rest_framework.permissions import IsAuthenticated

from .models import Collection, CollectionItem
from .permissions import IsOwner
from .serializers import (
    CollectionCreateSerializer,
    CollectionDetailSerializer,
    CollectionItemReadSerializer,
    CollectionItemWriteSerializer,
    CollectionListSerializer,
    CollectionUpdateSerializer,
)


@extend_schema(tags=["Collections"])
class CollectionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return (
            Collection.objects.filter(owner=self.request.user)
            .annotate(items_count=Count("items"))
            .order_by("-is_default", "-created_at")
        )

    def get_serializer_class(self):
        serializer_map = {
            "list": CollectionListSerializer,
            "retrieve": CollectionDetailSerializer,
            "create": CollectionCreateSerializer,
            "update": CollectionUpdateSerializer,
            "partial_update": CollectionUpdateSerializer,
        }
        return serializer_map.get(self.action, CollectionListSerializer)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        if (
            instance.is_default
            and Collection.objects.filter(owner=instance.owner).exclude(pk=instance.pk).exists()
            is False
        ):
            raise serializers.ValidationError("Can't delete the only/default collection.")
        super().perform_destroy(instance)


@extend_schema(tags=["Collection Items"])
class CollectionItemViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CollectionItemReadSerializer
        return CollectionItemWriteSerializer

    def _get_collection(self):
        collection_id = self.kwargs["collection_pk"]
        return get_object_or_404(Collection, pk=collection_id, owner=self.request.user)

    def get_queryset(self):
        collection = self._get_collection()
        return (
            CollectionItem.objects.filter(collection=collection)
            .select_related("post", "collection")
            .order_by("position", "-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["collection"] = self._get_collection()
        return ctx

    def perform_create(self, serializer):
        collection = self._get_collection()

        with transaction.atomic():
            # If client didn't send position, append to end.
            if serializer.validated_data.get("position") in (None, ""):
                max_pos = (
                    CollectionItem.objects.filter(collection=collection)
                    .aggregate(m=Max("position"))
                    .get("m")
                )
                serializer.validated_data["position"] = (max_pos or 0) + 1

            serializer.save(collection=collection)
