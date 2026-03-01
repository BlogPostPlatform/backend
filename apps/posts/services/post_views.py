import logging

from apps.posts.models import Post

logger = logging.getLogger(__name__)


def _get_redis():
    """Return a Redis connection or None if unavailable (e.g. in tests)."""
    try:
        from django_redis import get_redis_connection

        return get_redis_connection("default")
    except (NotImplementedError, Exception):
        return None


def register_post_view(post_id: int, viewer_id: str):
    """
    Adds a view (unique + total) for the given post.
    Silently skips when Redis is unavailable.
    """
    redis = _get_redis()
    if redis is None:
        return
    pipe = redis.pipeline()
    pipe.incr(f"post:{post_id}:views_total")
    pipe.sadd(f"post:{post_id}:views_unique", viewer_id)
    pipe.execute()


def get_post_views(post_id: int):
    """
    Returns (total_views, unique_views) from Redis + DB combined.
    Falls back to DB-only counts when Redis is unavailable.
    """
    # Get DB counts
    try:
        post = Post.objects.only("views_count_total", "views_count_unique").get(pk=post_id)
        total_db = post.views_count_total
        unique_db = post.views_count_unique
    except Post.DoesNotExist:
        total_db = 0
        unique_db = 0

    redis = _get_redis()
    if redis is None:
        return total_db, unique_db

    pipe = redis.pipeline()
    pipe.get(f"post:{post_id}:views_total")
    pipe.scard(f"post:{post_id}:views_unique")
    pipe.get(f"post:{post_id}:unique_baseline")

    total_redis, unique_current, baseline = pipe.execute()

    # Combine: DB (historical) + Redis (recent)
    total_combined = total_db + int(total_redis or 0)

    # For unique: DB has baseline + only NEW unique viewers count
    baseline = int(baseline or 0)
    unique_current = int(unique_current or 0)
    unique_delta = max(0, unique_current - baseline)  # New viewers since last flush
    unique_combined = unique_db + unique_delta

    return total_combined, unique_combined
