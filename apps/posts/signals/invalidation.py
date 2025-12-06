from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from apps.posts.models import Post, Reaction
from apps.posts.utils.invalidation import (
    invalidate_post_cache,
    invalidate_post_list_caches,
    invalidate_reaction_cache,
)


@receiver(post_save, sender=Post)
def post_saved(sender, instance, created, **kwargs):
    """
    Invalidate caches when a post is created or updated.
    """
    # Invalidate the specific post cache
    invalidate_post_cache(instance)

    # Invalidate list caches (latest, trending, popular, etc.)
    invalidate_post_list_caches()


@receiver(post_delete, sender=Post)
def post_deleted(sender, instance, **kwargs):
    """
    Invalidate caches when a post is deleted.
    """
    invalidate_post_cache(instance)
    invalidate_post_list_caches()


@receiver(m2m_changed, sender=Post.tags.through)
def post_tags_changed(sender, instance, action, **kwargs):
    """
    Invalidate post cache when tags are added/removed.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        invalidate_post_cache(instance)


@receiver(m2m_changed, sender=Post.allowed_reactions.through)
def post_reactions_changed(sender, instance, action, **kwargs):
    """
    Invalidate reaction cache when allowed reactions change.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        invalidate_reaction_cache(instance)


@receiver(post_save, sender=Reaction)
def reaction_saved(sender, instance, **kwargs):
    """
    Invalidate reaction cache when a reaction is created/updated.
    """
    invalidate_reaction_cache(instance.post, instance.user.id)


@receiver(post_delete, sender=Reaction)
def reaction_deleted(sender, instance, **kwargs):
    """
    Invalidate reaction cache when a reaction is deleted.
    """
    invalidate_reaction_cache(instance.post, instance.user.id)
