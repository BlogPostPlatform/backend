from django.db import IntegrityError, models

from apps.categories.models import Category
from apps.common.models import BaseModel
from apps.common.utils.files import unique_image_path
from apps.common.utils.utils import generate_unique_slug
from apps.users.models import User

from .managers import PublishedPostManager


class Post(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=150)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True
    )
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    short_description = models.TextField()

    content = models.JSONField(default=dict, blank=True)

    cover_image = models.ImageField(upload_to=unique_image_path, null=True, blank=True)

    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    published = PublishedPostManager()
    objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["slug"]),
        ]
        db_table = "Posts"
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self.__class__, self.title, allow_unicode=True)
        try:
            return super().save(*args, **kwargs)
        except IntegrityError:
            if not self.slug:
                self.slug = generate_unique_slug(self.__class__, self.title, allow_unicode=True)
                return super().save(*args, **kwargs)
            raise

    def __str__(self):
        return self.title
