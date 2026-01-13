from django_redis import get_redis_connection

from apps.posts.models import Post

redis = get_redis_connection("default")


def register_post_view(post_id: int, viewer_id: str):
    """
    Adds a view (unique + total) for the given post.
    """
    pipe = redis.pipeline()
    pipe.incr(f"post:{post_id}:views_total")
    pipe.sadd(f"post:{post_id}:views_unique", viewer_id)
    pipe.execute()


def get_post_views(post_id: int):
    """
    Returns (total_views, unique_views) from Redis + DB combined.
    """
    pipe = redis.pipeline()
    pipe.get(f"post:{post_id}:views_total")
    pipe.scard(f"post:{post_id}:views_unique")
    pipe.get(f"post:{post_id}:unique_baseline")

    total_redis, unique_current, baseline = pipe.execute()

    # Get DB counts
    try:
        post = Post.objects.only("views_count_total", "views_count_unique").get(pk=post_id)
        total_db = post.views_count_total
        unique_db = post.views_count_unique
    except Post.DoesNotExist:
        total_db = 0
        unique_db = 0

    # Combine: DB (historical) + Redis (recent)
    total_combined = total_db + int(total_redis or 0)

    # For unique: DB has baseline + only NEW unique viewers count
    baseline = int(baseline or 0)
    unique_current = int(unique_current or 0)
    unique_delta = max(0, unique_current - baseline)  # New viewers since last flush
    unique_combined = unique_db + unique_delta

    return total_combined, unique_combined
