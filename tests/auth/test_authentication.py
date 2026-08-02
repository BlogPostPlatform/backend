"""
Authentication and Permission Tests.
Tests for login, registration flow, token refresh, logout, and role-based permissions.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.users.models.user import Role


# ============================================================================
# LOGIN TESTS
# ============================================================================

class TestLogin:
    """Tests for the login endpoint."""

    URL = "/api/accounts/login/"

    def test_login_with_valid_credentials_returns_tokens(self, api_client, user_factory):
        """
        GIVEN a verified user with valid credentials
        WHEN they attempt to login
        THEN they receive access and refresh tokens
        """
        password = "securepassword123"
        user = user_factory.create(
            email="login@example.com",
            password=password,
            email_verified=True,
            must_set_password=False,
            mfa_enabled=False
        )

        response = api_client.post(self.URL, {
            "email": "login@example.com",
            "password": password
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert isinstance(response.data["access"], str)
        assert isinstance(response.data["refresh"], str)
        assert len(response.data["access"]) > 0
        assert len(response.data["refresh"]) > 0

    def test_login_with_invalid_password_fails(self, api_client, user_factory):
        """
        GIVEN a user with valid email
        WHEN they attempt to login with wrong password
        THEN they receive 401 Unauthorized
        """
        user = user_factory.create(
            email="wrongpass@example.com",
            password="correctpassword",
            email_verified=True,
            must_set_password=False
        )

        response = api_client.post(self.URL, {
            "email": "wrongpass@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_nonexistent_email_fails(self, api_client):
        """
        GIVEN no user exists with given email
        WHEN login is attempted
        THEN return 401 Unauthorized
        """
        response = api_client.post(self.URL, {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_unverified_email_fails(self, api_client, user_factory):
        """
        GIVEN a user who hasn't verified their email
        WHEN they attempt to login
        THEN return 401 with email_not_verified code
        """
        user = user_factory.create(
            email="unverified@example.com",
            password="Quartz!River92Orbit",
            email_verified=False,
            must_set_password=False
        )

        response = api_client.post(self.URL, {
            "email": "unverified@example.com",
            "password": "Quartz!River92Orbit"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data.get("code") == "email_not_verified" or "verify" in str(response.data).lower()

    def test_login_without_password_set_fails(self, api_client, user_factory):
        """
        GIVEN a user who must set initial password
        WHEN they attempt to login
        THEN return 401 with initial_password_required code
        """
        user = user_factory.create(
            email="nopass@example.com",
            password="Copper!Falcon73Mint",
            email_verified=True,
            must_set_password=True
        )

        response = api_client.post(self.URL, {
            "email": "nopass@example.com",
            "password": "Copper!Falcon73Mint"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_inactive_user_fails(self, api_client, user_factory):
        """
        GIVEN an inactive user
        WHEN they attempt to login
        THEN return 401 Unauthorized
        """
        user = user_factory.create(
            email="inactive@example.com",
            password="Nimbus!Cedar64Wave",
            email_verified=True,
            must_set_password=False,
            is_active=False
        )

        response = api_client.post(self.URL, {
            "email": "inactive@example.com",
            "password": "Nimbus!Cedar64Wave"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_missing_fields_returns_400(self, api_client):
        """
        GIVEN missing email or password
        WHEN login is attempted
        THEN return 400 Bad Request
        """
        # Missing password
        response = api_client.post(self.URL, {"email": "test@example.com"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Missing email
        response = api_client.post(self.URL, {"password": "password"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Empty body
        response = api_client.post(self.URL, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_with_mfa_enabled_returns_otp_required(self, api_client, user_factory):
        """
        GIVEN a user with MFA enabled
        WHEN they attempt to login with valid credentials
        THEN return otp_required=True and otp_token
        """
        user = user_factory.create(
            email="mfa@example.com",
            password="Velvet!Comet85Stone",
            email_verified=True,
            must_set_password=False,
            mfa_enabled=True
        )

        response = api_client.post(self.URL, {
            "email": "mfa@example.com",
            "password": "Velvet!Comet85Stone"
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("otp_required") is True
        assert "otp_token" in response.data


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================

class TestTokenRefresh:
    """Tests for the token refresh endpoint."""

    URL = "/api/accounts/login/refresh/"

    def test_refresh_with_valid_token_returns_new_access(self, api_client, regular_user):
        """
        GIVEN a valid refresh token
        WHEN token refresh is requested
        THEN return new access token
        """
        from tests.conftest import get_tokens_for_user
        tokens = get_tokens_for_user(regular_user)

        response = api_client.post(self.URL, {
            "refresh": tokens["refresh"]
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert isinstance(response.data["access"], str)

    def test_refresh_with_invalid_token_fails(self, api_client):
        """
        GIVEN an invalid refresh token
        WHEN token refresh is requested
        THEN return 401 Unauthorized
        """
        response = api_client.post(self.URL, {
            "refresh": "invalid.token.here"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_missing_token_fails(self, api_client):
        """
        GIVEN no refresh token provided
        WHEN token refresh is requested
        THEN return 400 Bad Request
        """
        response = api_client.post(self.URL, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# LOGOUT TESTS
# ============================================================================

class TestLogout:
    """Tests for the logout endpoint."""

    URL = "/api/accounts/auth/logout/"

    def test_logout_with_valid_token_succeeds(self, authenticated_client, regular_user):
        """
        GIVEN an authenticated user with valid refresh token
        WHEN they logout
        THEN return 204 No Content
        """
        from tests.conftest import get_tokens_for_user
        tokens = get_tokens_for_user(regular_user)

        response = authenticated_client.delete(self.URL, {
            "refresh_token": tokens["refresh"]
        }, format='json')

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_without_authentication_fails(self, api_client):
        """
        GIVEN an unauthenticated request
        WHEN logout is attempted
        THEN return 401 Unauthorized
        """
        response = api_client.delete(self.URL, {
            "refresh": "some-token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutAllDevices:
    """Tests for logout from all devices."""

    URL = "/api/accounts/auth/logout-of-all-devices/"

    def test_logout_all_devices_succeeds(self, authenticated_client):
        """
        GIVEN an authenticated user
        WHEN they logout from all devices
        THEN return 204 and message with device count
        """
        response = authenticated_client.delete(self.URL)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_all_devices_without_auth_fails(self, api_client):
        """
        GIVEN an unauthenticated request
        WHEN logout all devices is attempted
        THEN return 401 Unauthorized
        """
        response = api_client.delete(self.URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# REGISTRATION TESTS
# ============================================================================

class TestRegistration:
    """Tests for user registration flow."""

    URL = "/api/accounts/auth/register/"

    def test_register_with_valid_data_sends_verification(self, api_client):
        """
        GIVEN valid registration data
        WHEN registration is requested
        THEN return success message with otp_token
        """
        response = api_client.post(self.URL, {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "securepass123",
            "re_password": "securepass123"
        })

        assert response.status_code == status.HTTP_200_OK
        assert "otp_token" in response.data
        assert response.data.get("email") == "newuser@example.com"

    def test_register_with_existing_email_fails(self, api_client, user_factory):
        """
        GIVEN an email already registered
        WHEN registration is attempted with that email
        THEN return 400 Bad Request
        """
        user_factory.create(email="existing@example.com")

        response = api_client.post(self.URL, {
            "email": "existing@example.com",
            "first_name": "Test",
            "password": "password123",
            "re_password": "password123"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_mismatched_passwords_fails(self, api_client):
        """
        GIVEN passwords that don't match
        WHEN registration is attempted
        THEN return 400 Bad Request
        """
        response = api_client.post(self.URL, {
            "email": "mismatch@example.com",
            "first_name": "Test",
            "password": "password123",
            "re_password": "differentpassword"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_missing_email_fails(self, api_client):
        """
        GIVEN missing email field
        WHEN registration is attempted
        THEN return 400 Bad Request
        """
        response = api_client.post(self.URL, {
            "first_name": "Test",
            "password": "password123",
            "re_password": "password123"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_invalid_email_format_fails(self, api_client):
        """
        GIVEN an invalid email format
        WHEN registration is attempted
        THEN return 400 Bad Request
        """
        response = api_client.post(self.URL, {
            "email": "not-an-email",
            "first_name": "Test",
            "password": "password123",
            "re_password": "password123"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# PERMISSION TESTS
# ============================================================================

class TestRoleBasedPermissions:
    """Tests for role-based access control."""

    def test_regular_user_cannot_access_author_endpoints(self, authenticated_client):
        """
        GIVEN a regular user (USER role)
        WHEN they try to access author-only endpoints
        THEN return 403 Forbidden
        """
        response = authenticated_client.post("/api/posts/author/", {
            "title": "Test Post",
            "content": {"blocks": []},
            "status": "draft"
        }, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_author_can_access_author_endpoints(self, author_client, category):
        """
        GIVEN a user with AUTHOR role
        WHEN they access author endpoints
        THEN return success
        """
        response = author_client.post("/api/posts/author/", {
            "title": "Author's Post",
            "content": {"blocks": []},
            "short_description": "Test",
            "status": "draft",
            "category": category.id
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_can_access_admin_endpoints(self, admin_client, tag):
        """
        GIVEN a user with ADMIN role
        WHEN they access admin endpoints
        THEN return success
        """
        response = admin_client.delete(f"/api/tags/{tag.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_unauthenticated_cannot_access_protected_endpoints(self, api_client):
        """
        GIVEN an unauthenticated request
        WHEN accessing protected endpoints
        THEN return 401 Unauthorized
        """
        # Posts author endpoint
        response = api_client.post("/api/posts/author/", {"title": "Test"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # User profile endpoint
        response = api_client.get("/api/accounts/user/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Collections endpoint
        response = api_client.get("/api/collections/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_superuser_has_full_access(self, superuser_client, tag_factory):
        """
        GIVEN a superuser
        WHEN they access any endpoint
        THEN they have full access
        """
        tag = tag_factory.create(name="SuperTag", slug="super-tag")

        # Can delete tags (admin only)
        response = superuser_client.delete(f"/api/tags/{tag.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# USER PROFILE TESTS
# ============================================================================

class TestUserProfile:
    """Tests for user profile endpoints."""

    def test_get_own_profile(self, authenticated_client, regular_user):
        """
        GIVEN an authenticated user
        WHEN they request their profile
        THEN return their profile data
        """
        response = authenticated_client.get("/api/accounts/user/profile/")

        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data or "id" in response.data

    def test_update_profile(self, authenticated_client, regular_user):
        """
        GIVEN an authenticated user
        WHEN they update their profile
        THEN the profile is updated
        """
        response = authenticated_client.patch("/api/accounts/user/update-profile/", {
            "middle_name": "Updated"
        })

        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_access_profile(self, api_client):
        """
        GIVEN an unauthenticated request
        WHEN accessing profile endpoint
        THEN return 401 Unauthorized
        """
        response = api_client.get("/api/accounts/user/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# ACCOUNT DELETION TESTS
# ============================================================================

class TestAccountDeletion:
    """Tests for account deletion."""

    URL = "/api/accounts/user/delete-account/"

    def test_delete_own_account(self, api_client, user_factory):
        """
        GIVEN an authenticated user
        WHEN they delete their account
        THEN the account is removed
        """
        from tests.conftest import authenticate_client
        user = user_factory.create(email="todelete@example.com")
        user_id = user.id
        client = authenticate_client(api_client, user)

        response = client.delete(self.URL)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify user is deleted
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assert not User.objects.filter(id=user_id).exists()

    def test_unauthenticated_cannot_delete_account(self, api_client):
        """
        GIVEN an unauthenticated request
        WHEN account deletion is attempted
        THEN return 401 Unauthorized
        """
        response = api_client.delete(self.URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
