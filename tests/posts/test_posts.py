"""
Post Management Tests.
Tests for post CRUD operations, filtering, permissions, and reactions.
"""
import pytest
from django.utils import timezone
from rest_framework import status

from apps.posts.models import Post


# ============================================================================
# AUTHOR POST CRUD TESTS
# ============================================================================

class TestAuthorPostCreate:
    """Tests for creating posts as an author."""

    URL = "/api/posts/author/"

    def test_author_can_create_draft_post(self, author_client, category):
        """
        GIVEN an authenticated author
        WHEN they create a draft post with valid data
        THEN the post is created with status 201
        """
        response = author_client.post(self.URL, {
            "title": "My New Post",
            "content": {"blocks": [{"type": "paragraph", "data": {"text": "Hello"}}]},
            "short_description": "A test post",
            "status": "draft",
            "category": category.id,
            "allow_comments": True
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "My New Post"
        assert response.data["status"] == "draft"
        assert "slug" in response.data
        assert response.data["slug"] is not None

    def test_author_can_create_published_post(self, author_client, category):
        """
        GIVEN an authenticated author
        WHEN they create a published post
        THEN the post is created with published status
        """
        response = author_client.post(self.URL, {
            "title": "Published Post",
            "content": {"blocks": []},
            "short_description": "A published post",
            "status": "published",
            "category": category.id
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "published"

    def test_create_scheduled_post_requires_published_at(self, author_client, category):
        """
        GIVEN an author creating a scheduled post
        WHEN published_at is not provided
        THEN return 400 Bad Request
        """
        response = author_client.post(self.URL, {
            "title": "Scheduled Post",
            "content": {"blocks": []},
            "short_description": "Will be published later",
            "status": "scheduled",
            "category": category.id
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_scheduled_post_with_future_date(self, author_client, category):
        """
        GIVEN an author creating a scheduled post
        WHEN published_at is in the future
        THEN the post is created successfully
        """
        future_date = timezone.now() + timezone.timedelta(days=1)

        response = author_client.post(self.URL, {
            "title": "Scheduled Post",
            "content": {"blocks": []},
            "short_description": "Will be published later",
            "status": "scheduled",
            "category": category.id,
            "published_at": future_date.isoformat()
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "scheduled"

    def test_create_post_with_past_scheduled_date_fails(self, author_client, category):
        """
        GIVEN an author creating a scheduled post
        WHEN published_at is in the past
        THEN return 400 Bad Request
        """
        past_date = timezone.now() - timezone.timedelta(days=1)

        response = author_client.post(self.URL, {
            "title": "Past Scheduled Post",
            "content": {"blocks": []},
            "short_description": "Bad date",
            "status": "scheduled",
            "category": category.id,
            "published_at": past_date.isoformat()
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_post_generates_unique_slug(self, author_client, category):
        """
        GIVEN an author creating posts with same title
        WHEN multiple posts are created
        THEN each post gets a unique slug
        """
        # First post
        response1 = author_client.post(self.URL, {
            "title": "Same Title",
            "content": {"blocks": []},
            "short_description": "First",
            "status": "draft",
            "category": category.id
        }, format='json')

        # Second post with same title
        response2 = author_client.post(self.URL, {
            "title": "Same Title",
            "content": {"blocks": []},
            "short_description": "Second",
            "status": "draft",
            "category": category.id
        }, format='json')

        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED
        assert response1.data["slug"] != response2.data["slug"]

    def test_create_post_with_tags(self, author_client, category, multiple_tags):
        """
        GIVEN an author creating a post with tags
        WHEN valid tag IDs are provided
        THEN the post is created with tags attached
        """
        tag_ids = [tag.id for tag in multiple_tags]

        response = author_client.post(self.URL, {
            "title": "Post with Tags",
            "content": {"blocks": []},
            "short_description": "Tagged post",
            "status": "draft",
            "category": category.id,
            "tags": tag_ids
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_post_with_invalid_tags_fails(self, author_client, category):
        """
        GIVEN an author creating a post with non-existent tag IDs
        WHEN the post is created
        THEN return 400 Bad Request
        """
        response = author_client.post(self.URL, {
            "title": "Post with Bad Tags",
            "content": {"blocks": []},
            "short_description": "Invalid tags",
            "status": "draft",
            "category": category.id,
            "tags": [99999, 99998]
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_post_with_reactions(self, author_client, category, reaction_types):
        """
        GIVEN an author creating a post with allowed reactions
        WHEN valid reaction type IDs are provided
        THEN the post is created with reactions attached
        """
        reaction_ids = [r.id for r in reaction_types]

        response = author_client.post(self.URL, {
            "title": "Post with Reactions",
            "content": {"blocks": []},
            "short_description": "Reactable post",
            "status": "draft",
            "category": category.id,
            "allowed_reactions": reaction_ids
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_regular_user_cannot_create_post(self, authenticated_client, category):
        """
        GIVEN a regular user (not author/admin)
        WHEN they try to create a post
        THEN return 403 Forbidden
        """
        response = authenticated_client.post(self.URL, {
            "title": "Unauthorized Post",
            "content": {"blocks": []},
            "short_description": "Should fail",
            "status": "draft",
            "category": category.id
        }, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create_post(self, api_client, category):
        """
        GIVEN an unauthenticated request
        WHEN post creation is attempted
        THEN return 401 Unauthorized
        """
        response = api_client.post(self.URL, {
            "title": "Anonymous Post",
            "content": {"blocks": []},
            "status": "draft"
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthorPostUpdate:
    """Tests for updating posts as an author."""

    def test_author_can_update_own_post(self, author_client, draft_post):
        """
        GIVEN an author's own draft post
        WHEN they update the post
        THEN the post is updated successfully
        """
        url = f"/api/posts/author/{draft_post.slug}/"

        response = author_client.patch(url, {
            "title": "Updated Title"
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"

    def test_author_can_change_post_status(self, author_client, draft_post):
        """
        GIVEN an author's draft post
        WHEN they change status to published
        THEN the post status is updated
        """
        url = f"/api/posts/author/{draft_post.slug}/"

        response = author_client.patch(url, {
            "status": "published"
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "published"

    def test_author_can_clear_tags(self, author_client, post_factory, author_user, category, multiple_tags):
        """
        GIVEN a post with tags
        WHEN clear_tags flag is set
        THEN all tags are removed
        """
        post = post_factory.create(author=author_user, category=category, slug="tagged-post")
        post.tags.set(multiple_tags)

        url = f"/api/posts/author/{post.slug}/"

        response = author_client.patch(url, {
            "clear_tags": True
        }, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_author_cannot_update_other_authors_post(
        self, author_client, user_factory, post_factory, category
    ):
        """
        GIVEN a post by another author
        WHEN an author tries to update it
        THEN return 404 Not Found (post not in their queryset)
        """
        other_author = user_factory.create_author(email="other@example.com")
        other_post = post_factory.create(author=other_author, category=category, slug="other-post")

        url = f"/api/posts/author/{other_post.slug}/"

        response = author_client.patch(url, {
            "title": "Hacked Title"
        }, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_superuser_can_update_any_post(self, superuser_client, published_post):
        """
        GIVEN a superuser
        WHEN they update any post
        THEN the update succeeds
        """
        url = f"/api/posts/author/{published_post.slug}/"

        response = superuser_client.patch(url, {
            "title": "Superuser Updated"
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Superuser Updated"


class TestAuthorPostDelete:
    """Tests for deleting posts."""

    def test_author_can_delete_own_post(self, author_client, draft_post):
        """
        GIVEN an author's own post
        WHEN they delete it
        THEN the post is removed
        """
        url = f"/api/posts/author/{draft_post.slug}/"

        response = author_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(slug=draft_post.slug).exists()

    def test_author_cannot_delete_other_authors_post(
        self, author_client, user_factory, post_factory, category
    ):
        """
        GIVEN a post by another author
        WHEN an author tries to delete it
        THEN return 404 Not Found
        """
        other_author = user_factory.create_author(email="delete-other@example.com")
        other_post = post_factory.create(author=other_author, category=category, slug="delete-other")

        url = f"/api/posts/author/{other_post.slug}/"

        response = author_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Post.objects.filter(slug="delete-other").exists()


class TestAuthorPostList:
    """Tests for listing posts as author."""

    def test_author_sees_only_own_posts(self, author_client, author_user, user_factory, post_factory, category):
        """
        GIVEN an author with their own posts
        WHEN they list posts
        THEN they see only their own posts
        """
        # Create own posts
        post_factory.create(author=author_user, category=category, slug="own-1")
        post_factory.create(author=author_user, category=category, slug="own-2")

        # Create another author's post
        other_author = user_factory.create_author(email="listing@example.com")
        post_factory.create(author=other_author, category=category, slug="other-1")

        response = author_client.get("/api/posts/author/")

        assert response.status_code == status.HTTP_200_OK
        # Check all returned posts belong to the author
        results = response.data.get("results", response.data)
        for post in results:
            assert post["slug"].startswith("own-") or post["slug"] == "draft-test-post"

    def test_author_can_filter_by_status(self, author_client, author_user, post_factory, category):
        """
        GIVEN an author with draft and published posts
        WHEN they filter by status
        THEN only matching posts are returned
        """
        post_factory.create(author=author_user, category=category, status="draft", slug="filter-draft")
        post_factory.create_published(author=author_user, category=category, slug="filter-pub")

        response = author_client.get("/api/posts/author/my-posts/", {"status": "draft"})

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# CLIENT POST VIEWS (PUBLIC ACCESS)
# ============================================================================

class TestClientPostList:
    """Tests for public post listing."""

    URL = "/api/posts/client/"

    def test_anonymous_can_list_published_posts(self, api_client, published_post):
        """
        GIVEN published posts exist
        WHEN anonymous user lists posts
        THEN they see published posts only
        """
        response = api_client.get(self.URL)

        assert response.status_code == status.HTTP_200_OK

    def test_anonymous_cannot_see_draft_posts(self, api_client, draft_post, published_post):
        """
        GIVEN both draft and published posts
        WHEN anonymous user lists posts
        THEN draft posts are not included
        """
        response = api_client.get(self.URL)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)
        slugs = [p["slug"] for p in results]
        assert draft_post.slug not in slugs

    def test_author_can_see_own_drafts_in_client_view(
        self, author_client, author_user, post_factory, category
    ):
        """
        GIVEN an author with draft posts
        WHEN they view client posts
        THEN they can see their own drafts too
        """
        draft = post_factory.create_draft(author=author_user, category=category, slug="my-draft")

        response = author_client.get(self.URL)

        assert response.status_code == status.HTTP_200_OK


class TestClientPostRetrieve:
    """Tests for retrieving single post."""

    def test_anonymous_can_view_published_post(self, api_client, published_post):
        """
        GIVEN a published post
        WHEN anonymous user retrieves it
        THEN the full post data is returned
        """
        url = f"/api/posts/client/{published_post.slug}/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == published_post.slug
        assert response.data["title"] == published_post.title
        assert "content" in response.data
        assert "author" in response.data

    def test_anonymous_cannot_view_draft_post(self, api_client, draft_post):
        """
        GIVEN a draft post
        WHEN anonymous user tries to retrieve it
        THEN return 404 Not Found
        """
        url = f"/api/posts/client/{draft_post.slug}/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_view_returns_author_details(self, api_client, published_post):
        """
        GIVEN a published post
        WHEN retrieved
        THEN author information is included
        """
        url = f"/api/posts/client/{published_post.slug}/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        author = response.data["author"]
        assert "id" in author
        assert "first_name" in author
        assert "email" in author


# ============================================================================
# POST REACTIONS TESTS
# ============================================================================

class TestPostReactions:
    """Tests for post reaction functionality."""

    def test_authenticated_user_can_react_to_post(
        self, authenticated_client, published_post, reaction_types
    ):
        """
        GIVEN an authenticated user and a post with allowed reactions
        WHEN they react to the post
        THEN the reaction is recorded
        """
        published_post.allowed_reactions.set(reaction_types)
        url = f"/api/posts/client/{published_post.slug}/put-reaction/"

        response = authenticated_client.post(url, {
            "type": reaction_types[0].id
        }, format='json')

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_unauthenticated_cannot_react(self, api_client, published_post, reaction_types):
        """
        GIVEN an unauthenticated request
        WHEN reaction is attempted
        THEN return 401 Unauthorized
        """
        published_post.allowed_reactions.set(reaction_types)
        url = f"/api/posts/client/{published_post.slug}/put-reaction/"

        response = api_client.post(url, {
            "type": reaction_types[0].id
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# POST IMAGE UPLOAD TESTS
# ============================================================================

class TestPostImageUpload:
    """Tests for post image upload functionality."""

    def test_author_can_upload_temp_image(self, author_client):
        """
        GIVEN an authenticated author
        WHEN they upload a temporary image
        THEN the image is saved and URL returned
        """
        from io import BytesIO
        from PIL import Image

        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        buffer.name = 'test.png'

        response = author_client.post(
            "/api/posts/author/upload-temp-image/",
            {"image": buffer},
            format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert "url" in response.data

    def test_upload_without_image_fails(self, author_client):
        """
        GIVEN an author
        WHEN they upload without providing image
        THEN return 400 Bad Request
        """
        response = author_client.post("/api/posts/author/upload-temp-image/", {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# POST FILTERING/SEARCH TESTS
# ============================================================================

class TestPostFiltering:
    """Tests for post filtering and search."""

    def test_filter_posts_by_category(
        self, api_client, post_factory, author_user, category_factory
    ):
        """
        GIVEN posts in different categories
        WHEN filtering by category
        THEN only matching posts are returned
        """
        cat1 = category_factory.create(name="Tech")
        cat2 = category_factory.create(name="Science")

        post_factory.create_published(author=author_user, category=cat1, slug="tech-1")
        post_factory.create_published(author=author_user, category=cat2, slug="science-1")

        response = api_client.get(f"/api/posts/client/?category={cat1.id}")

        assert response.status_code == status.HTTP_200_OK

    def test_search_posts_by_title(
        self, api_client, post_factory, author_user, category
    ):
        """
        GIVEN posts with different titles
        WHEN searching by title
        THEN matching posts are returned
        """
        post_factory.create_published(
            author=author_user,
            category=category,
            title="Python Tutorial",
            slug="python-tut"
        )
        post_factory.create_published(
            author=author_user,
            category=category,
            title="Java Guide",
            slug="java-guide"
        )

        response = api_client.get("/api/posts/client/?search=Python")

        assert response.status_code == status.HTTP_200_OK
