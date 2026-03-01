"""
Shared fixtures and factories for all tests.
Uses pytest-django and factory_boy for deterministic test data.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.categories.models import Category
from apps.collection.models import Collection, CollectionItem
from apps.comments.models import Comment, CommentReaction
from apps.notifications.models import CommentNotification
from apps.posts.models import Post, ReactionType
from apps.tags.models import Tag
from apps.users.models import UserProfile
from apps.users.models.user import Role

User = get_user_model()


# ============================================================================
# Pytest Configuration
# ============================================================================

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Automatically enable database access for all tests."""
    pass


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


# ============================================================================
# User Factories & Fixtures
# ============================================================================

class UserFactory:
    """Factory for creating User instances with different roles."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(
        cls,
        email=None,
        password="testpass123",
        first_name="Test",
        last_name="User",
        role=Role.USER,
        email_verified=True,
        must_set_password=False,
        is_active=True,
        is_superuser=False,
        **kwargs
    ):
        counter = cls._get_counter()
        if email is None:
            email = f"testuser{counter}@example.com"

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            email_verified=email_verified,
            must_set_password=must_set_password,
            is_active=is_active,
            is_superuser=is_superuser,
            **kwargs
        )
        # Profile is auto-created by CustomUserManager.create_user
        return user

    @classmethod
    def create_admin(cls, **kwargs):
        return cls.create(role=Role.ADMIN, **kwargs)

    @classmethod
    def create_author(cls, **kwargs):
        return cls.create(role=Role.AUTHOR, **kwargs)

    @classmethod
    def create_superuser(cls, **kwargs):
        return cls.create(is_superuser=True, role=Role.ADMIN, **kwargs)


@pytest.fixture
def user_factory():
    """Return UserFactory for creating users in tests."""
    return UserFactory


@pytest.fixture
def regular_user(user_factory):
    """Create a regular user with USER role."""
    return user_factory.create(
        email="regular@example.com",
        first_name="Regular",
        last_name="User",
        role=Role.USER
    )


@pytest.fixture
def author_user(user_factory):
    """Create a user with AUTHOR role."""
    return user_factory.create(
        email="author@example.com",
        first_name="Author",
        last_name="User",
        role=Role.AUTHOR
    )


@pytest.fixture
def admin_user(user_factory):
    """Create a user with ADMIN role."""
    return user_factory.create_admin(
        email="admin@example.com",
        first_name="Admin",
        last_name="User"
    )


@pytest.fixture
def superuser(user_factory):
    """Create a superuser."""
    return user_factory.create_superuser(
        email="superuser@example.com",
        first_name="Super",
        last_name="User"
    )


@pytest.fixture
def unverified_user(user_factory):
    """Create a user who hasn't verified their email."""
    return user_factory.create(
        email="unverified@example.com",
        email_verified=False,
        must_set_password=True
    )


# ============================================================================
# Authentication Helpers
# ============================================================================

def get_tokens_for_user(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Return an API client authenticated as a regular user."""
    tokens = get_tokens_for_user(regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    api_client.user = regular_user
    return api_client


@pytest.fixture
def author_client(api_client, author_user):
    """Return an API client authenticated as an author."""
    tokens = get_tokens_for_user(author_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    api_client.user = author_user
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an API client authenticated as an admin."""
    tokens = get_tokens_for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    api_client.user = admin_user
    return api_client


@pytest.fixture
def superuser_client(api_client, superuser):
    """Return an API client authenticated as a superuser."""
    tokens = get_tokens_for_user(superuser)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    api_client.user = superuser
    return api_client


def authenticate_client(api_client, user):
    """Helper to authenticate any client with any user."""
    tokens = get_tokens_for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    api_client.user = user
    return api_client


# ============================================================================
# Category Factory & Fixtures
# ============================================================================

class CategoryFactory:
    """Factory for creating Category instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(cls, name=None, description=None, **kwargs):
        counter = cls._get_counter()
        if name is None:
            name = f"Category {counter}"
        if description is None:
            description = f"Description for category {counter}"

        return Category.objects.create(
            name=name,
            description=description,
            **kwargs
        )


@pytest.fixture
def category_factory():
    """Return CategoryFactory for creating categories in tests."""
    return CategoryFactory


@pytest.fixture
def category(category_factory):
    """Create a single category."""
    return category_factory.create(name="Test Category")


# ============================================================================
# Tag Factory & Fixtures
# ============================================================================

class TagFactory:
    """Factory for creating Tag instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(cls, name=None, slug=None, **kwargs):
        counter = cls._get_counter()
        if name is None:
            name = f"Tag{counter}"
        if slug is None:
            slug = f"tag-{counter}"

        return Tag.objects.create(name=name, slug=slug, **kwargs)


@pytest.fixture
def tag_factory():
    """Return TagFactory for creating tags in tests."""
    return TagFactory


@pytest.fixture
def tag(tag_factory):
    """Create a single tag."""
    return tag_factory.create(name="TestTag", slug="test-tag")


@pytest.fixture
def multiple_tags(tag_factory):
    """Create multiple tags for testing."""
    return [
        tag_factory.create(name="Python", slug="python"),
        tag_factory.create(name="Django", slug="django"),
        tag_factory.create(name="REST", slug="rest"),
    ]


# ============================================================================
# Post Factory & Fixtures
# ============================================================================

class PostFactory:
    """Factory for creating Post instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(
        cls,
        author,
        title=None,
        slug=None,
        category=None,
        status=Post.Status.PUBLISHED,
        content=None,
        short_description=None,
        allow_comments=True,
        **kwargs
    ):
        counter = cls._get_counter()
        if title is None:
            title = f"Test Post {counter}"
        if slug is None:
            slug = f"test-post-{counter}"
        if content is None:
            content = {"blocks": [{"type": "paragraph", "data": {"text": f"Content {counter}"}}]}
        if short_description is None:
            short_description = f"Short description for post {counter}"

        post = Post.objects.create(
            author=author,
            title=title,
            slug=slug,
            category=category,
            status=status,
            content=content,
            short_description=short_description,
            allow_comments=allow_comments,
            **kwargs
        )
        return post

    @classmethod
    def create_draft(cls, author, **kwargs):
        return cls.create(author=author, status=Post.Status.DRAFT, **kwargs)

    @classmethod
    def create_published(cls, author, **kwargs):
        from django.utils import timezone
        return cls.create(
            author=author,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
            **kwargs
        )


@pytest.fixture
def post_factory():
    """Return PostFactory for creating posts in tests."""
    return PostFactory


@pytest.fixture
def published_post(post_factory, author_user, category):
    """Create a published post."""
    return post_factory.create_published(
        author=author_user,
        category=category,
        title="Published Test Post",
        slug="published-test-post"
    )


@pytest.fixture
def draft_post(post_factory, author_user, category):
    """Create a draft post."""
    return post_factory.create_draft(
        author=author_user,
        category=category,
        title="Draft Test Post",
        slug="draft-test-post"
    )


@pytest.fixture
def post_without_comments(post_factory, author_user, category):
    """Create a post with comments disabled."""
    return post_factory.create_published(
        author=author_user,
        category=category,
        allow_comments=False,
        title="No Comments Post",
        slug="no-comments-post"
    )


# ============================================================================
# Comment Factory & Fixtures
# ============================================================================

class CommentFactory:
    """Factory for creating Comment instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(cls, post, author, content=None, parent=None, **kwargs):
        counter = cls._get_counter()
        if content is None:
            content = f"Test comment {counter}"

        return Comment.objects.create(
            post=post,
            author=author,
            content=content,
            parent=parent,
            **kwargs
        )

    @classmethod
    def create_reply(cls, parent_comment, author, content=None, **kwargs):
        return cls.create(
            post=parent_comment.post,
            author=author,
            content=content,
            parent=parent_comment,
            **kwargs
        )


@pytest.fixture
def comment_factory():
    """Return CommentFactory for creating comments in tests."""
    return CommentFactory


@pytest.fixture
def comment(comment_factory, published_post, regular_user):
    """Create a single comment on a published post."""
    return comment_factory.create(
        post=published_post,
        author=regular_user,
        content="This is a test comment"
    )


@pytest.fixture
def comment_with_replies(comment_factory, published_post, regular_user, author_user):
    """Create a comment with replies."""
    parent = comment_factory.create(
        post=published_post,
        author=regular_user,
        content="Parent comment"
    )
    reply1 = comment_factory.create_reply(
        parent_comment=parent,
        author=author_user,
        content="First reply"
    )
    reply2 = comment_factory.create_reply(
        parent_comment=parent,
        author=regular_user,
        content="Second reply"
    )
    return {'parent': parent, 'replies': [reply1, reply2]}


# ============================================================================
# Comment Reaction Fixtures
# ============================================================================

class CommentReactionFactory:
    """Factory for creating CommentReaction instances."""

    @classmethod
    def create_like(cls, user, comment):
        return CommentReaction.objects.create(
            user=user,
            comment=comment,
            reaction=CommentReaction.CommentReactionType.LIKE
        )

    @classmethod
    def create_dislike(cls, user, comment):
        return CommentReaction.objects.create(
            user=user,
            comment=comment,
            reaction=CommentReaction.CommentReactionType.DISLIKE
        )


@pytest.fixture
def comment_reaction_factory():
    """Return CommentReactionFactory for creating reactions in tests."""
    return CommentReactionFactory


# ============================================================================
# Collection Factory & Fixtures
# ============================================================================

class CollectionFactory:
    """Factory for creating Collection instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(
        cls,
        owner,
        name=None,
        slug=None,
        visibility="PRIVATE",
        description=None,
        is_default=False,
        **kwargs
    ):
        counter = cls._get_counter()
        if name is None:
            name = f"Collection {counter}"
        if slug is None:
            slug = f"collection-{counter}"
        if description is None:
            description = f"Description for collection {counter}"

        return Collection.objects.create(
            owner=owner,
            name=name,
            slug=slug,
            visibility=visibility,
            description=description,
            is_default=is_default,
            **kwargs
        )

    @classmethod
    def create_default(cls, owner, **kwargs):
        # Clear any existing default first
        Collection.objects.filter(owner=owner, is_default=True).update(is_default=False)
        return cls.create(owner=owner, is_default=True, name="Default Collection", **kwargs)


@pytest.fixture
def collection_factory():
    """Return CollectionFactory for creating collections in tests."""
    return CollectionFactory


@pytest.fixture
def collection(collection_factory, regular_user):
    """Create a single collection for a regular user."""
    return collection_factory.create(
        owner=regular_user,
        name="My Collection",
        slug="my-collection"
    )


@pytest.fixture
def default_collection(collection_factory, regular_user):
    """Create a default collection for a regular user."""
    return collection_factory.create_default(owner=regular_user)


# ============================================================================
# Collection Item Factory & Fixtures
# ============================================================================

class CollectionItemFactory:
    """Factory for creating CollectionItem instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(cls, collection, post, note=None, position=None, **kwargs):
        counter = cls._get_counter()
        if note is None:
            note = f"Note {counter}"
        if position is None:
            position = counter

        return CollectionItem.objects.create(
            collection=collection,
            post=post,
            note=note,
            position=position,
            **kwargs
        )


@pytest.fixture
def collection_item_factory():
    """Return CollectionItemFactory for creating collection items."""
    return CollectionItemFactory


@pytest.fixture
def collection_with_items(collection_factory, collection_item_factory, regular_user, post_factory, author_user, category):
    """Create a collection with multiple items."""
    collection = collection_factory.create(owner=regular_user)
    posts = [
        post_factory.create_published(author=author_user, category=category)
        for _ in range(3)
    ]
    items = [
        collection_item_factory.create(collection=collection, post=post, position=i+1)
        for i, post in enumerate(posts)
    ]
    return {'collection': collection, 'items': items, 'posts': posts}


# ============================================================================
# Notification Factory & Fixtures
# ============================================================================

class NotificationFactory:
    """Factory for creating CommentNotification instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(
        cls,
        receiver,
        sender,
        comment,
        message=None,
        is_read=False,
        **kwargs
    ):
        counter = cls._get_counter()
        if message is None:
            message = f"Notification message {counter}"

        return CommentNotification.objects.create(
            receiver=receiver,
            sender=sender,
            comment=comment,
            message=message,
            is_read=is_read,
            **kwargs
        )


@pytest.fixture
def notification_factory():
    """Return NotificationFactory for creating notifications."""
    return NotificationFactory


@pytest.fixture
def notification(notification_factory, comment, regular_user, author_user):
    """Create a single notification."""
    return notification_factory.create(
        receiver=regular_user,
        sender=author_user,
        comment=comment,
        message="Someone replied to your comment"
    )


@pytest.fixture
def multiple_notifications(notification_factory, comment_factory, published_post, regular_user, author_user, user_factory):
    """Create multiple notifications for testing pagination and bulk operations."""
    notifications = []
    for i in range(5):
        comment = comment_factory.create(
            post=published_post,
            author=author_user,
            content=f"Comment {i}"
        )
        notification = notification_factory.create(
            receiver=regular_user,
            sender=author_user,
            comment=comment,
            message=f"Notification {i}",
            is_read=(i % 2 == 0)  # Alternate read/unread
        )
        notifications.append(notification)
    return notifications


# ============================================================================
# Reaction Type Factory & Fixtures
# ============================================================================

class ReactionTypeFactory:
    """Factory for creating ReactionType instances."""

    _counter = 0

    @classmethod
    def _get_counter(cls):
        cls._counter += 1
        return cls._counter

    @classmethod
    def create(cls, name=None, emoji=None, **kwargs):
        counter = cls._get_counter()
        if name is None:
            name = f"reaction_{counter}"
        if emoji is None:
            emoji = "👍"

        return ReactionType.objects.create(name=name, emoji=emoji, **kwargs)


@pytest.fixture
def reaction_type_factory():
    """Return ReactionTypeFactory for creating reaction types."""
    return ReactionTypeFactory


@pytest.fixture
def reaction_types(reaction_type_factory):
    """Create common reaction types."""
    return [
        reaction_type_factory.create(name="like", emoji="👍"),
        reaction_type_factory.create(name="love", emoji="❤️"),
        reaction_type_factory.create(name="laugh", emoji="😂"),
    ]
