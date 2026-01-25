from django.db import models
from django.db.models import Q

from apps.common.models import BaseModel


class VisibilityChoices(models.TextChoices):
    PUBLIC = "PUBLIC", "Public"
    PRIVATE = "PRIVATE", "Private"


class Collection(BaseModel):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="collections",
    )
    slug = models.SlugField(max_length=200)
    visibility = models.CharField(
        max_length=15,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PRIVATE,
    )
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"'{self.name}' -> {self.owner.email}"

    class Meta:
        db_table = "Collections"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="uq_collection_owner_name",
            ),
            models.UniqueConstraint(
                fields=["owner", "slug"],
                name="uq_collection_owner_slug",
            ),
            models.UniqueConstraint(
                fields=["owner"],
                condition=Q(is_default=True),
                name="uq_collection_one_default_per_owner",
            ),
        ]


class CollectionItem(BaseModel):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="items",
    )
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="+")
    note = models.CharField(max_length=300, blank=True)
    position = models.PositiveIntegerField(null=True, blank=True)  # optional

    def __str__(self):
        return f"{self.collection.name} - {self.post.title} for user id: {self.collection.owner_id}"

    class Meta:
        db_table = "collection_item"
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "post"],
                name="uq_collectionitem_collection_post",
            ),
            # If you truly implement ordering:
            # models.UniqueConstraint(
            #     fields=["collection", "position"],
            #     name="uq_collectionitem_collection_position",
            #     condition=Q(position__isnull=False),
            # ),
        ]
        indexes = [
            models.Index(fields=["collection", "created_at"]),
        ]
