from django.core.cache import cache
from django.db import IntegrityError, models

from apps.categories.models import Category
from apps.common.models import BaseModel
from apps.common.utils.files import unique_image_path
from apps.common.utils.utils import generate_unique_slug
from apps.posts.utils import calculate_read_time, extract_readable_text
from apps.tags.models import Tag
from apps.users.models import User
from core.storages import PublicMediaStorage

from .managers import PublishedPostManager
from .reactions import ReactionType


class Post(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        SCHEDULED = "scheduled", "Scheduled"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=150)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True
    )
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    short_description = models.TextField(null=True, blank=True)

    content = models.JSONField(default=dict, blank=True, help_text="Raw JSON formatted content")
    text_content = models.TextField(null=True, blank=True, help_text="Text formatted content")

    cover_image = models.ImageField(
        storage=PublicMediaStorage(), upload_to=unique_image_path, null=True, blank=True
    )

    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    allowed_reactions = models.ManyToManyField(
        ReactionType, blank=True, related_name="posts_allowed"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    allow_comments = models.BooleanField(default=True)

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
        if self.content:
            try:
                self.text_content = extract_readable_text(self.content)
            except Exception as e:
                # Log but don't crash
                print(f"Error extracting text for post {self.pk}: {e}")
                self.text_content = ""

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

    @property
    def read_time(self):
        cache_key = f"post:{self.pk}:read_time"
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        if not self.text_content:
            return 0

        try:
            minutes = calculate_read_time(self.text_content)
        except Exception:
            minutes = 0

        # Cache for 24 hours
        cache.set(cache_key, minutes, 60 * 60 * 24)
        return minutes
