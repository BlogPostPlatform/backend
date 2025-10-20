import logging

import requests
from decouple import config
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenViewBase

from apps.users.models import User, UserProfile
from apps.users.serializers import (
    CheckTokenBeforeObtainSerializer,
    ConfirmEmailChangeSerializer,
    CustomTokenRefreshSerializer,
    ForgotPasswordSerializer,
    LogoutSerializer,
    RegisterSerializer,
    RequestEmailChangeSerializer,
    ResetPasswordSerializer,
    SetInitialPasswordSerializer,
    UserProfileReadSerializer,
    UserProfileWriteSerializer,
    UserSerializer,
    ValidateInviteSerializer,
    VerifyPasswordResetSerializer,
    VerifyRegisterSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["Auth"])
class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.none()

    def get_serializer_class(self):
        if self.action == "register":
            return RegisterSerializer
        elif self.action == "verify_registration":
            return VerifyRegisterSerializer
        elif self.action == "forgot_password":
            return ForgotPasswordSerializer
        elif self.action == "verify_password_reset":
            return VerifyPasswordResetSerializer
        elif self.action == "reset_password":
            return ResetPasswordSerializer
        elif self.action == "logout":
            return LogoutSerializer
        return RegisterSerializer

    def get_permissions(self):
        if self.action in ["logout", "logout_of_all_devices"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=False, methods=["post"])
    @method_decorator(transaction.atomic)
    def register(self, request):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="verify-registration")
    @method_decorator(transaction.atomic)
    def verify_registration(self, request):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="forgot-password")
    @method_decorator(transaction.atomic)
    def forgot_password(self, request):
        logger.info("users.forgot_password. Request forgot password start.")
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        logger.info("users.forgot_password. Email sent.")
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="verify-password-reset")
    @method_decorator(transaction.atomic)
    def verify_password_reset(self, request):
        logger.info("users.verify_password_reset. verify code for forgot password start.")
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        logger.info("users.verify_password_reset. tokens sent.")
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="reset-password")
    @method_decorator(transaction.atomic)
    def reset_password(self, request):
        logger.info("users.reset_password... reset password start.")
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        logger.info("users.reset_password... reset password completed.")
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"])
    @method_decorator(transaction.atomic)
    def logout(self, request):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        logger.info("users.logout. user id=%s", self.request.user.pk)
        return Response({"message": "Logout successful."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["delete"], url_path="logout-of-all-devices")
    @method_decorator(transaction.atomic)
    def logout_of_all_devices(self, request):
        user = request.user
        tokens = OutstandingToken.objects.filter(user=user)
        i = 0
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
            i += 1
        logger.info(f"users.logout-of-all-devices. User logged out of {i} devices.")
        return Response(
            {"message": f"Successfully logged out of {i} devices."},
            status=status.HTTP_204_NO_CONTENT,
        )


@extend_schema(tags=["User"])
class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "update_profile":
            return UserProfileWriteSerializer
        elif self.action == "profile":
            return UserProfileReadSerializer
        elif self.action == "request_email_change":
            return RequestEmailChangeSerializer
        elif self.action == "confirm_email_change":
            return ConfirmEmailChangeSerializer
        return UserSerializer

    @action(detail=False, methods=["get"])
    def profile(self, request):
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            logger.warning("users.profile. UserProfile DoesNotExist")
            return Response({"message": "User has no profile."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @extend_schema(responses=UserProfileReadSerializer)
    @action(
        detail=False,
        methods=["put", "patch"],
        parser_classes=(MultiPartParser, FormParser, JSONParser),
        url_path="update-profile",
    )
    @method_decorator(transaction.atomic)
    def update_profile(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = self.get_serializer(
            instance=profile,
            data=request.data,
            partial=(request.method == "PATCH"),
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response = UserProfileReadSerializer(instance, context=self.get_serializer_context())
        logger.info(f"users.update_profile. User with id {request.user.pk} updated profile.")
        return Response(response.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="request-email-change")
    @method_decorator(transaction.atomic)
    def request_email_change(self, request):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="confirm-email-change")
    @method_decorator(transaction.atomic)
    def confirm_email_change(self, request):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        logger.info(
            f"users.confirm_email_change. Confirm email change successful"
            f" for user id {request.user.pk}"
        )
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Google Login"])
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # state = token_urlsafe(24)
        auth_url = (
            f"{config('GOOGLE_AUTH_URL')}"
            f"?client_id={config('GOOGLE_CLIENT_ID')}"
            f"&redirect_uri={config('GOOGLE_REDIRECT_URI')}"
            f"&response_type=code"
            f"&scope=openid email profile"
            # f"&state={state}"
        )

        return redirect(auth_url)


@extend_schema(tags=["Google Login"])
class GoogleCallBackView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(transaction.atomic)
    def get(self, request):
        code = request.GET.get("code")
        token_data = {
            "code": code,
            "client_id": config("GOOGLE_CLIENT_ID"),
            "client_secret": config("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": config("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }

        token_response = requests.post(config("GOOGLE_TOKEN_URL"), data=token_data)
        token_json = token_response.json()
        access_token = token_json.get("access_token")

        user_info_response = requests.get(
            config("GOOGLE_USER_INFO_URL"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        user_info = user_info_response.json()

        google_user_id = user_info.get("sub")
        first_name = user_info.get("name", None)
        last_name = user_info.get("given_name", None)
        email = user_info.get("email")

        if User.objects.filter(email=email, google_id__isnull=True).exists():
            return Response({"You already in the system. Please login in a standard way."})

        user, created = User.objects.get_or_create(
            google_id=google_user_id,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        if created:
            user.set_unusable_password()
            user.save()

            frontend_url = config("FRONTEND_URL", default="http://localhost:8080")
            redirect_url = (
                f"{frontend_url}/register/complete-profile?access_token={str(access)}"
                f"&refresh_token={str(refresh)}&email={email}&message=Registration "
                f"completed successfully"
            )
            return redirect(redirect_url)

        frontend_url = config("FRONTEND_URL", default="http://localhost:8080")
        redirect_url = (
            f"{frontend_url}/oauth/google/callback?access_token={access}"
            f"&refresh_token={refresh}&email={email}"
        )
        return redirect(redirect_url)


@extend_schema(tags=["Google Login"])
class CompleteGoogleRegistration(APIView):
    permission_classes = [AllowAny]

    @method_decorator(transaction.atomic)
    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()

        if not user:
            return Response(f"User with {email} email not found.", status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "success"})


@extend_schema(tags=["Auth"], request=SetInitialPasswordSerializer)
class SetInitialPasswordView(APIView):
    """
    Response format:
    "message": "success",
    "tokens": {
        "refresh": "token",
        "access": "token"
    }
    """

    permission_classes = [AllowAny]

    @method_decorator(transaction.atomic)
    def post(self, request):
        serializer = SetInitialPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        logger.info(
            f"users.SetInitialPassword. Initial password for user id {user.pk} set successfully"
        )
        return Response(
            {
                "message": "Password set successfully. You can now log in.",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Auth"], request=ValidateInviteSerializer)
class ValidateInviteView(APIView):
    """
    Response format:
    "valid": boolean,
    "errors": "errors"
    """

    permission_classes = [AllowAny]

    def post(self, request):
        s = ValidateInviteSerializer(data=request.query_params)
        logger.info("users.ValidateInvite. requested.")
        if s.is_valid():
            return Response({"valid": True})
        return Response({"valid": False, "errors": s.errors}, status=200)


@extend_schema(tags=["Auth"])
class CheckTokenBeforeObtainView(TokenViewBase):
    permission_classes = [AllowAny]
    serializer_class = CheckTokenBeforeObtainSerializer


@extend_schema(tags=["Auth"])
class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
