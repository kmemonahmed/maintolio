from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    ChangePasswordSerializer,
    LogoutSerializer,
    MeSerializer,
    OrganizationRegisterSerializer,
)

class CustomTokenObtainPairView(TokenObtainPairView):
    @extend_schema(
        tags=["Auth"],
        summary="Login",
        description="Authenticate user and return access and refresh tokens.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Auth"],
        summary="Refresh access token",
        description="Use a valid refresh token to get a new access token.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

# Organization Register
class OrganizationRegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register a new organization",
        request=OrganizationRegisterSerializer,
    )
    def post(self, request):
        serializer = OrganizationRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        user = result["user"]
        organization = result["organization"]
        membership = result["membership"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Organization registered successfully.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone": user.phone,
                },
                "organization": {
                    "id": organization.id,
                    "name": organization.name,
                    "slug": organization.slug,
                },
                "membership": {
                    "id": membership.id,
                    "role": membership.role,
                },
            },
            status=status.HTTP_201_CREATED,
        )


# Profile view
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Get current user profile",
        responses=MeSerializer,
    )
    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


# Change Password
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Change password",
        description="Allows an authenticated user to change their password.",
        request=ChangePasswordSerializer,
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


# Logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Logout",
        description="Blacklists the provided refresh token. Existing access token remains valid until expiry.",
        request=LogoutSerializer,
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )