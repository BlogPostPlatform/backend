import logging

from celery import shared_task
from django.utils import timezone

from .models import Post

logger = logging.getLogger(__name__)


@shared_task
def publish_scheduled_posts():
    now = timezone.now()

    posts = Post.objects.filter(
        status=Post.Status.SCHEDULED,
        published_at__lte=now,
    )

    count = posts.update(status=Post.Status.PUBLISHED)

    logger.info("Published %d posts.", count)
    return f"Published {count} posts."
