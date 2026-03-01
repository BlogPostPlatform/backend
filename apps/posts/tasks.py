import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django_redis import get_redis_connection

from .models import Post

logger = logging.getLogger(__name__)


redis = SimpleLazyObject(lambda: get_redis_connection("default"))


@shared_task
def publish_scheduled_posts():
    now = timezone.now()

    posts = Post.objects.filter(
        status=Post.Status.SCHEDULED,
        published_at__lte=now,
    )
    try:
        count = posts.update(status=Post.Status.PUBLISHED)
    except Exception as e:
        logger.error(e)
        return "Error occurred while publishing scheduled posts."

    if count > 0:
        logger.info("Published %d scheduled posts.", count)

    return f"Published {count} posts."


@shared_task
def flush_post_views_to_db():
    """
    Flush Redis view counts to DB. Call this from your cron job.
    Uses delta tracking for unique views to preserve deduplication.
    """
    pattern = "post:*:views_total"
    cursor = 0
    flushed_count = 0

    while True:
        cursor, keys = redis.scan(cursor, match=pattern, count=100)

        for key in keys:
            # Extract post_id from key like "post:123:views_total"
            post_id = int(key.decode().split(":")[1])
            if flush(post_id):
                flushed_count += 1

        if cursor == 0:
            break

    logger.warning(f"Flush completed: {flushed_count} posts updated")
    return flushed_count


def flush(post_id: int) -> bool:
    pipe = redis.pipeline()
    pipe.get(f"post:{post_id}:views_total")
    pipe.scard(f"post:{post_id}:views_unique")
    pipe.get(f"post:{post_id}:unique_baseline")

    total_redis, unique_current, baseline = pipe.execute()

    total_redis = int(total_redis or 0)
    unique_current = int(unique_current or 0)
    baseline = int(baseline or 0)

    # Nothing to flush
    if total_redis == 0 and unique_current == baseline:
        return False

    # Calculate delta for unique views
    unique_delta = max(0, unique_current - baseline)

    try:
        with transaction.atomic():
            # Use F() expressions for atomic increment
            from django.db.models import F

            updated = Post.objects.filter(pk=post_id).update(
                views_count_total=F("views_count_total") + total_redis,
                views_count_unique=F("views_count_unique") + unique_delta,
            )

            if updated == 0:
                logger.warning(f"Post {post_id} not found during flush")
                return False

            # After successful DB write, reset Redis counters
            pipe = redis.pipeline()
            pipe.set(f"post:{post_id}:views_total", 0)  # Reset total
            pipe.set(f"post:{post_id}:unique_baseline", unique_current)  # Update baseline
            # DON'T delete the unique set - keeps deduplication working!
            pipe.execute()

            logger.info(f"Flushed post {post_id}: +{total_redis} total, +{unique_delta} unique")
            # Invalidate most popular posts cache after DB update
            from django.core.cache import cache

            from apps.users.models.user import Role

            roles = ["anon", Role.ADMIN, Role.AUTHOR]
            cache_keys = [f"most_popular_posts:{role}" for role in roles]
            cache.delete_many(cache_keys)
            logger.info(f"Invalidated most popular posts cache after flush for post {post_id}")
            return True

    except Exception as e:
        logger.error(f"Failed to flush views for post {post_id}: {e}")
        return False
