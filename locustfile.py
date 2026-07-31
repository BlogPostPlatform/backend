# flake8: noqa
"""
Locust Load Testing Suite for Blog Website API
================================================

This file contains comprehensive load tests for the blog application with realistic
user behavior patterns. Delete this file when you're done with stress testing.

Installation:
    uv sync --locked

Usage:
    # Basic run (starts web UI at http://localhost:8089)
    uv run locust -f locustfile.py

    # Headless mode (no web UI)
    uv run locust -f locustfile.py --headless -u 100 -r 10 --run-time 5m

    # Target specific host
    uv run locust -f locustfile.py --host http://localhost:8000

Options:
    -u, --users       Number of concurrent users
    -r, --spawn-rate  Users spawned per second
    --run-time        Stop after this time (e.g., 5m, 1h)
    --headless        Run without web UI

Delete Instructions:
    Simply delete this file when done: rm locustfile.py
"""

import random
import string
import time

from locust import HttpUser, between, events, tag, task
from locust.exception import StopUser

# ============================================================================
# Configuration
# ============================================================================

# Test user credentials - update these with valid test accounts in your DB
TEST_USERS = [
    {"email": "vbahodir00@gmail.com", "password": "12"},
    {"email": "vbahodir0@gmail.com", "password": "12"},
    {"email": "cajavif772@hudisk.com", "password": "12"},
]

# API base paths
API_PREFIX = "/api"


def random_string(length=8):
    """Generate random string for test data"""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_email():
    """Generate random email for registration tests"""
    return f"loadtest_{random_string(10)}@example.com"


# ============================================================================
# Mixins for Shared Behavior
# ============================================================================


class AuthMixin:
    """Mixin providing authentication capabilities"""

    access_token = None
    refresh_token = None
    is_authenticated = False

    def login(self, email=None, password=None):
        """Authenticate user and store tokens"""
        if email is None or password is None:
            creds = random.choice(TEST_USERS)
            email = creds["email"]
            password = creds["password"]

        with self.client.post(
            f"{API_PREFIX}/accounts/login/",
            json={"email": email, "password": password},
            name="[Auth] Login",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access")
                self.refresh_token = data.get("refresh")
                self.is_authenticated = True
                response.success()
            elif response.status_code == 401:
                # Expected for invalid credentials during load test
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    def refresh_tokens(self):
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return False

        with self.client.post(
            f"{API_PREFIX}/accounts/login/refresh/",
            json={"refresh": self.refresh_token},
            name="[Auth] Token Refresh",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access")
                response.success()
                return True
            else:
                response.failure(f"Token refresh failed: {response.status_code}")
                return False

    def logout(self):
        """Logout and invalidate tokens"""
        if not self.refresh_token:
            return

        headers = self._auth_headers()
        with self.client.delete(
            f"{API_PREFIX}/accounts/auth/logout/",
            json={"refresh": self.refresh_token},
            headers=headers,
            name="[Auth] Logout",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 204]:
                self.access_token = None
                self.refresh_token = None
                self.is_authenticated = False
                response.success()

    def _auth_headers(self):
        """Get authorization headers"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}


# ============================================================================
# Anonymous User (Browsing without authentication)
# ============================================================================


class AnonymousBrowserUser(HttpUser):
    """
    Simulates anonymous users browsing the blog.
    This is the most common user type - people just reading content.
    Weight: 60% of traffic
    """

    weight = 6
    wait_time = between(2, 8)

    post_slugs = []
    category_ids = []
    tag_ids = []

    def on_start(self):
        """Fetch initial data for navigation"""
        self._fetch_posts()
        self._fetch_categories()
        self._fetch_tags()

    def _fetch_posts(self):
        """Fetch list of posts to get slugs for detail views"""
        with self.client.get(
            f"{API_PREFIX}/posts/client/",
            name="[Posts] List (Initial)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", data) if isinstance(data, dict) else data
                if isinstance(results, list):
                    self.post_slugs = [p.get("slug") for p in results if p.get("slug")]
                response.success()

    def _fetch_categories(self):
        """Fetch categories"""
        with self.client.get(
            f"{API_PREFIX}/category/",
            name="[Categories] List",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", data) if isinstance(data, dict) else data
                if isinstance(results, list):
                    self.category_ids = [c.get("id") for c in results if c.get("id")]
                response.success()

    def _fetch_tags(self):
        """Fetch tags"""
        with self.client.get(
            f"{API_PREFIX}/tags/",
            name="[Tags] List",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", data) if isinstance(data, dict) else data
                if isinstance(results, list):
                    self.tag_ids = [t.get("id") for t in results if t.get("id")]
                response.success()

    @task(10)
    @tag("posts", "read", "high-traffic")
    def browse_posts_list(self):
        """Browse paginated post list - most common action"""
        page = random.randint(1, 5)
        self.client.get(
            f"{API_PREFIX}/posts/client/?page={page}",
            name="[Posts] List (Paginated)",
        )

    @task(8)
    @tag("posts", "read", "high-traffic")
    def view_post_detail(self):
        """View a specific post - second most common action"""
        if not self.post_slugs:
            self._fetch_posts()
            return

        slug = random.choice(self.post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/",
            name="[Posts] Detail",
        )

    @task(6)
    @tag("posts", "read")
    def view_latest_posts(self):
        """View latest posts section"""
        self.client.get(
            f"{API_PREFIX}/posts/client/latest-posts/",
            name="[Posts] Latest",
        )

    @task(5)
    @tag("posts", "read")
    def view_trending_posts(self):
        """View trending posts"""
        self.client.get(
            f"{API_PREFIX}/posts/client/trending-posts/",
            name="[Posts] Trending",
        )

    @task(5)
    @tag("posts", "read")
    def view_most_popular(self):
        """View most popular posts"""
        self.client.get(
            f"{API_PREFIX}/posts/client/most-popular-posts/",
            name="[Posts] Most Popular",
        )

    @task(4)
    @tag("posts", "read")
    def view_related_posts(self):
        """View related posts for a specific post"""
        if not self.post_slugs:
            return

        slug = random.choice(self.post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/related-posts/",
            name="[Posts] Related Posts",
        )

    @task(4)
    @tag("comments", "read")
    def view_post_comments(self):
        """View comments on a post"""
        if not self.post_slugs:
            return

        slug = random.choice(self.post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/comments/",
            name="[Comments] List",
        )

    @task(3)
    @tag("posts", "read")
    def view_post_reactions(self):
        """View reactions on a post"""
        if not self.post_slugs:
            return

        slug = random.choice(self.post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/list-reactions/",
            name="[Posts] Reactions List",
        )

    @task(3)
    @tag("categories", "read")
    def browse_category(self):
        """Browse posts in a category"""
        if not self.category_ids:
            return

        cat_id = random.choice(self.category_ids)
        self.client.get(
            f"{API_PREFIX}/category/{cat_id}/posts/",
            name="[Categories] Category Posts",
        )

    @task(3)
    @tag("tags", "read")
    def browse_tag(self):
        """Browse posts with a specific tag"""
        if not self.tag_ids:
            return

        tag_id = random.choice(self.tag_ids)
        self.client.get(
            f"{API_PREFIX}/tags/{tag_id}/posts/",
            name="[Tags] Tag Posts",
        )

    @task(2)
    @tag("posts", "search")
    def search_posts(self):
        """Search for posts"""
        search_terms = ["python", "django", "web", "api", "tutorial", "guide", "how to"]
        term = random.choice(search_terms)
        self.client.get(
            f"{API_PREFIX}/posts/client/?search={term}",
            name="[Posts] Search",
        )

    @task(2)
    @tag("stats", "read")
    def view_homepage_stats(self):
        """View homepage statistics"""
        self.client.get(
            f"{API_PREFIX}/posts/client/homepage-statistics/",
            name="[Posts] Homepage Stats",
        )

    @task(1)
    @tag("health")
    def health_check(self):
        """Health check endpoint"""
        self.client.get(
            f"{API_PREFIX}/check-health/",
            name="[System] Health Check",
        )


# ============================================================================
# Authenticated Reader User
# ============================================================================


class AuthenticatedReaderUser(AuthMixin, HttpUser):
    """
    Simulates logged-in users reading and interacting with content.
    They favorite, bookmark, and react to posts.
    Weight: 25% of traffic
    """

    weight = 3
    wait_time = between(3, 10)

    post_slugs = []
    comment_ids = []

    def on_start(self):
        """Login and fetch initial data"""
        self.login()
        if self.is_authenticated:
            self._fetch_posts()

    def on_stop(self):
        """Logout on completion"""
        if self.is_authenticated:
            self.logout()

    def _fetch_posts(self):
        """Fetch posts with auth"""
        headers = self._auth_headers()
        with self.client.get(
            f"{API_PREFIX}/posts/client/",
            headers=headers,
            name="[Posts] List (Auth)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", data) if isinstance(data, dict) else data
                if isinstance(results, list):
                    self.post_slugs = [p.get("slug") for p in results if p.get("slug")]
                response.success()

    @task(8)
    @tag("posts", "read", "auth")
    def browse_posts(self):
        """Browse posts while authenticated"""
        headers = self._auth_headers()
        page = random.randint(1, 3)
        self.client.get(
            f"{API_PREFIX}/posts/client/?page={page}",
            headers=headers,
            name="[Posts] List (Auth)",
        )

    @task(7)
    @tag("posts", "read", "auth")
    def view_post_detail(self):
        """View post detail with user interaction data"""
        if not self.post_slugs:
            return

        headers = self._auth_headers()
        slug = random.choice(self.post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/",
            headers=headers,
            name="[Posts] Detail (Auth)",
        )

    @task(4)
    @tag("posts", "interaction", "auth")
    def toggle_favourite(self):
        """Favourite or unfavourite a post"""
        if not self.post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.post_slugs)

        # Random: add or remove favourite
        if random.random() > 0.5:
            self.client.post(
                f"{API_PREFIX}/posts/client/{slug}/favourite/",
                headers=headers,
                name="[Posts] Add Favourite",
            )
        else:
            self.client.delete(
                f"{API_PREFIX}/posts/client/{slug}/favourite/",
                headers=headers,
                name="[Posts] Remove Favourite",
            )

    @task(4)
    @tag("posts", "interaction", "auth")
    def toggle_bookmark(self):
        """Bookmark or unbookmark a post"""
        if not self.post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.post_slugs)

        if random.random() > 0.5:
            self.client.post(
                f"{API_PREFIX}/posts/client/{slug}/bookmark/",
                headers=headers,
                name="[Posts] Add Bookmark",
            )
        else:
            self.client.delete(
                f"{API_PREFIX}/posts/client/{slug}/bookmark/",
                headers=headers,
                name="[Posts] Remove Bookmark",
            )

    @task(3)
    @tag("posts", "reaction", "auth")
    def react_to_post(self):
        """Add reaction to a post"""
        if not self.post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.post_slugs)

        # First, get available reaction types
        with self.client.get(
            f"{API_PREFIX}/posts/author/list-available-reactions/",
            headers=headers,
            name="[Posts] Get Reaction Types",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                reactions = response.json()
                if reactions:
                    reaction_type = random.choice(reactions)
                    self.client.post(
                        f"{API_PREFIX}/posts/client/{slug}/put-reaction/",
                        headers=headers,
                        json={"type_id": reaction_type.get("id")},
                        name="[Posts] Add Reaction",
                    )
                response.success()

    @task(3)
    @tag("favourites", "read", "auth")
    def view_favourites(self):
        """View user's favourite posts"""
        if not self.is_authenticated:
            return

        headers = self._auth_headers()
        self.client.get(
            f"{API_PREFIX}/favourites/",
            headers=headers,
            name="[Favourites] List",
        )

    @task(3)
    @tag("bookmarks", "read", "auth")
    def view_bookmarks(self):
        """View user's bookmarked posts"""
        if not self.is_authenticated:
            return

        headers = self._auth_headers()
        self.client.get(
            f"{API_PREFIX}/bookmarks/",
            headers=headers,
            name="[Bookmarks] List",
        )

    @task(3)
    @tag("user", "read", "auth")
    def view_profile(self):
        """View own user profile"""
        if not self.is_authenticated:
            return

        headers = self._auth_headers()
        self.client.get(
            f"{API_PREFIX}/accounts/user/profile/",
            headers=headers,
            name="[User] View Profile",
        )

    @task(2)
    @tag("comments", "write", "auth")
    def post_comment(self):
        """Post a comment on a post"""
        if not self.post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.post_slugs)

        comment_texts = [
            "Great article! Thanks for sharing.",
            "Very informative, learned something new today.",
            "Could you elaborate more on this topic?",
            "I disagree with some points, but good read overall.",
            "This helped me solve my problem. Thank you!",
            "Looking forward to more content like this.",
            "Nice explanation, very clear and concise.",
        ]

        self.client.post(
            f"{API_PREFIX}/posts/client/{slug}/comments/",
            headers=headers,
            json={"content": random.choice(comment_texts)},
            name="[Comments] Create",
        )

    @task(2)
    @tag("comments", "interaction", "auth")
    def like_comment(self):
        """Like or dislike a comment"""
        if not self.post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.post_slugs)

        # First get comments
        with self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/comments/",
            headers=headers,
            name="[Comments] List (for interaction)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", data) if isinstance(data, dict) else data
                if isinstance(results, list) and results:
                    comment = random.choice(results)
                    comment_id = comment.get("id")
                    if comment_id:
                        action = random.choice(["like", "dislike"])
                        self.client.post(
                            f"{API_PREFIX}/posts/client/{slug}/comments/{comment_id}/{action}/",
                            headers=headers,
                            name=f"[Comments] {action.title()}",
                        )
                response.success()

    @task(1)
    @tag("auth", "refresh")
    def refresh_token(self):
        """Refresh authentication token"""
        if self.refresh_token:
            self.refresh_tokens()

    @task(2)
    @tag("notifications", "read", "auth")
    def view_notifications(self):
        """View user notifications"""
        if not self.is_authenticated:
            return

        headers = self._auth_headers()
        self.client.get(
            f"{API_PREFIX}/notifications/comment/",
            headers=headers,
            name="[Notifications] List",
        )


# ============================================================================
# Author User (Content Creator)
# ============================================================================


class AuthorUser(AuthMixin, HttpUser):
    """
    Simulates content authors creating and managing posts.
    Less frequent but heavier operations.
    Weight: 10% of traffic
    """

    weight = 1
    wait_time = between(5, 15)

    my_post_slugs = []

    def on_start(self):
        """Login as author and fetch own posts"""
        # Use author credentials if available
        author_creds = next(
            (u for u in TEST_USERS if "author" in u["email"].lower()),
            TEST_USERS[0] if TEST_USERS else None,
        )
        if author_creds:
            self.login(author_creds["email"], author_creds["password"])
        else:
            self.login()

        if self.is_authenticated:
            self._fetch_my_posts()

    def on_stop(self):
        """Logout on completion"""
        if self.is_authenticated:
            self.logout()

    def _fetch_my_posts(self):
        """Fetch author's own posts"""
        headers = self._auth_headers()
        with self.client.get(
            f"{API_PREFIX}/posts/author/my-posts/",
            headers=headers,
            name="[Author] My Posts",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", data) if isinstance(data, dict) else data
                if isinstance(results, list):
                    self.my_post_slugs = [p.get("slug") for p in results if p.get("slug")]
                response.success()
            elif response.status_code == 403:
                # User is not an author
                response.success()

    @task(5)
    @tag("author", "read")
    def view_my_posts(self):
        """View list of own posts"""
        if not self.is_authenticated:
            return

        headers = self._auth_headers()
        self.client.get(
            f"{API_PREFIX}/posts/author/my-posts/",
            headers=headers,
            name="[Author] My Posts",
        )

    @task(4)
    @tag("author", "read")
    def view_my_post_detail(self):
        """View detail of own post"""
        if not self.my_post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.my_post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/author/{slug}/",
            headers=headers,
            name="[Author] Post Detail",
        )

    @task(2)
    @tag("author", "write")
    def create_post(self):
        """Create a new post (draft)"""
        if not self.is_authenticated:
            return

        headers = self._auth_headers()

        # Get categories first
        with self.client.get(
            f"{API_PREFIX}/category/",
            headers=headers,
            name="[Categories] List (for create)",
            catch_response=True,
        ) as response:
            category_id = None
            if response.status_code == 200:
                categories = response.json()
                results = (
                    categories.get("results", categories)
                    if isinstance(categories, dict)
                    else categories
                )
                if isinstance(results, list) and results:
                    category_id = random.choice(results).get("id")
                response.success()

        if category_id:
            post_data = {
                "title": f"Load Test Post {random_string(8)}",
                "content": f"This is a test post created during load testing. Content: {random_string(200)}",
                "short_description": f"Test post short description {random_string(20)}",
                "category": category_id,
                "status": "draft",  # Keep as draft to avoid pollution
                "allow_comments": True,
            }

            self.client.post(
                f"{API_PREFIX}/posts/author/",
                headers=headers,
                json=post_data,
                name="[Author] Create Post",
            )

    @task(2)
    @tag("author", "write")
    def update_post(self):
        """Update an existing post"""
        if not self.my_post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.my_post_slugs)

        update_data = {
            "short_description": f"Updated description at {time.time()}",
        }

        self.client.patch(
            f"{API_PREFIX}/posts/author/{slug}/",
            headers=headers,
            json=update_data,
            name="[Author] Update Post",
        )

    @task(1)
    @tag("author", "read")
    def list_available_reactions(self):
        """List available reaction types"""
        if not self.is_authenticated:
            return

        headers = self._auth_headers()
        self.client.get(
            f"{API_PREFIX}/posts/author/list-available-reactions/",
            headers=headers,
            name="[Author] List Reactions",
        )

    @task(3)
    @tag("author", "read")
    def view_post_comments(self):
        """View comments on own posts"""
        if not self.my_post_slugs or not self.is_authenticated:
            return

        headers = self._auth_headers()
        slug = random.choice(self.my_post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/comments/",
            headers=headers,
            name="[Author] View Comments",
        )


# ============================================================================
# Spike User (Simulates viral content scenario)
# ============================================================================


class SpikeUser(HttpUser):
    """
    Simulates a spike in traffic when content goes viral.
    Focuses heavily on a few "hot" posts.
    Weight: 5% of traffic
    """

    weight = 1
    wait_time = between(0.5, 2)  # Very fast requests

    hot_post_slugs = []

    def on_start(self):
        """Fetch trending/popular posts as "hot" content"""
        with self.client.get(
            f"{API_PREFIX}/posts/client/most-popular-posts/",
            name="[Spike] Fetch Hot Posts",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.hot_post_slugs = [p.get("slug") for p in data[:3] if p.get("slug")]
                response.success()

    @task(10)
    @tag("spike", "posts")
    def view_hot_post(self):
        """Hammer a hot post - simulates viral traffic"""
        if not self.hot_post_slugs:
            return

        slug = random.choice(self.hot_post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/",
            name="[Spike] Hot Post View",
        )

    @task(5)
    @tag("spike", "comments")
    def view_hot_comments(self):
        """View comments on hot posts"""
        if not self.hot_post_slugs:
            return

        slug = random.choice(self.hot_post_slugs)
        self.client.get(
            f"{API_PREFIX}/posts/client/{slug}/comments/",
            name="[Spike] Hot Post Comments",
        )


# ============================================================================
# Event Hooks for Custom Reporting
# ============================================================================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("\n" + "=" * 60)
    print("🚀 Starting Blog Website Load Test")
    print("=" * 60)
    print("\nUser Distribution:")
    print("  - Anonymous Browsers: 60% (weight=6)")
    print("  - Authenticated Readers: 25% (weight=3)")
    print("  - Authors: 10% (weight=1)")
    print("  - Spike Users: 5% (weight=1)")
    print("\n" + "=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("\n" + "=" * 60)
    print("✅ Load Test Complete")
    print("=" * 60 + "\n")


# ============================================================================
# Quick Start Configuration
# ============================================================================

if __name__ == "__main__":
    import os
    import sys

    # Default configuration
    host = os.environ.get("LOCUST_HOST", "http://localhost:8000")

    print(
        f"""
╔══════════════════════════════════════════════════════════════╗
║           Blog Website Load Testing Suite                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Quick Start Commands:                                       ║
║                                                              ║
║  1. Web UI Mode (Recommended for first run):                 ║
║     locust -f locustfile.py --host {host}        ║
║                                                              ║
║  2. Headless Mode (for CI/CD):                               ║
║     locust -f locustfile.py --host {host} \\      ║
║            --headless -u 50 -r 5 --run-time 2m               ║
║                                                              ║
║  3. High Load Test:                                          ║
║     locust -f locustfile.py --host {host} \\      ║
║            --headless -u 500 -r 50 --run-time 10m            ║
║                                                              ║
║  Options:                                                    ║
║    -u, --users       Total concurrent users                  ║
║    -r, --spawn-rate  Users to spawn per second               ║
║    --run-time        Duration (e.g., 30s, 5m, 1h)            ║
║    --tags            Run only specific tagged tasks          ║
║                      e.g., --tags posts,auth                 ║
║                                                              ║
║  Environment Variables:                                      ║
║    LOCUST_HOST       Target host URL                         ║
║                                                              ║
║  📝 Note: Update TEST_USERS in this file with valid          ║
║     test accounts from your database for authenticated       ║
║     user testing.                                            ║
║                                                              ║
║  🗑️  To delete: Simply remove this file                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    )

    # Run locust
    sys.exit(os.system(f"locust -f {__file__} --host {host}"))
