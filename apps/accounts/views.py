from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    ChangePasswordSerializer,
    LogoutSerializer,
    MeSerializer,
    MaintolioTokenObtainPairSerializer,
    OrganizationRegisterSerializer,
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = MaintolioTokenObtainPairSerializer

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
class OrganizationRegisterView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OrganizationRegisterSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Register a new organization",
        request=OrganizationRegisterSerializer,
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
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
class MeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Get current user profile",
        responses=MeSerializer,
    )
    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


# Change Password
class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Change password",
        description="Allows an authenticated user to change their password.",
        request=ChangePasswordSerializer,
    )
    def post(self, request):
        serializer = self.get_serializer(
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
class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Logout",
        description="Blacklists the provided refresh token. Existing access token remains valid until expiry.",
        request=LogoutSerializer,
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )
