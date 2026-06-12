from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import OrganizationMembership
from .serializers import (
    TeamMemberCreateSerializer,
    TeamMemberSerializer,
    TeamMemberUpdateSerializer,
)
from .utils import get_current_membership, is_owner_or_admin
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import CurrentOrganizationResponseSerializer, OrganizationSerializer


class CurrentOrganizationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Organizations"],
        summary="Get current organization",
        description="Returns the current organization workspace and the user's membership role.",
        responses=CurrentOrganizationResponseSerializer,
    )
    def get(self, request):
        membership = get_current_membership(request)

        serializer = CurrentOrganizationResponseSerializer({
            "organization": membership.organization,
            "membership": membership,
        })

        return Response(serializer.data)

    @extend_schema(
        tags=["Organizations"],
        summary="Update current organization",
        description="Updates the current organization profile. Only OWNER and ADMIN can update.",
        request=OrganizationSerializer,
        responses=OrganizationSerializer,
    )
    def patch(self, request):
        membership = get_current_membership(request)

        if not is_owner_or_admin(membership):
            raise PermissionDenied(
                "Only organization owners and admins can update organization settings."
            )

        serializer = OrganizationSerializer(
            membership.organization,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)



VIEW_TEAM_ROLES = [
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.MANAGER,
]

MANAGE_TEAM_ROLES = [
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
]


class TeamMemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = OrganizationMembership.objects.none()
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filterset_fields = ["role", "is_active"]
    search_fields = [
        "user__email",
        "user__full_name",
        "user__phone",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "role",
    ]

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    def get_queryset(self):
        current_membership = self.get_current_membership()

        return (
            OrganizationMembership.objects
            .filter(organization=current_membership.organization)
            .select_related("user", "organization", "invited_by")
            .order_by("role", "user__email")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return TeamMemberCreateSerializer

        if self.action in ["partial_update", "update"]:
            return TeamMemberUpdateSerializer

        return TeamMemberSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_membership"] = self.get_current_membership()
        return context

    def require_roles(self, allowed_roles):
        current_membership = self.get_current_membership()

        if current_membership.role not in allowed_roles:
            raise PermissionDenied(
                "You do not have permission to perform this action."
            )

    @extend_schema(
        tags=["Team Members"],
        summary="List team members",
        responses=TeamMemberSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.require_roles(VIEW_TEAM_ROLES)
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Team Members"],
        summary="Retrieve team member",
        responses=TeamMemberSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        self.require_roles(VIEW_TEAM_ROLES)
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Team Members"],
        summary="Create team member",
        request=TeamMemberCreateSerializer,
        responses=TeamMemberSerializer,
    )
    def create(self, request, *args, **kwargs):
        self.require_roles(MANAGE_TEAM_ROLES)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = serializer.save()
        response_serializer = TeamMemberSerializer(membership)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Team Members"],
        summary="Update team member",
        request=TeamMemberUpdateSerializer,
        responses=TeamMemberSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        self.require_roles(MANAGE_TEAM_ROLES)

        membership = self.get_object()

        serializer = self.get_serializer(
            membership,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        membership = serializer.save()
        response_serializer = TeamMemberSerializer(membership)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Team Members"],
        summary="Deactivate team member",
        description="Soft-deactivates an organization membership instead of deleting it.",
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        self.require_roles(MANAGE_TEAM_ROLES)

        membership = self.get_object()
        current_membership = self.get_current_membership()

        if membership.id == current_membership.id:
            raise PermissionDenied(
                "You cannot deactivate your own membership."
            )

        if membership.role == OrganizationMembership.Role.OWNER:
            raise PermissionDenied(
                "Owner membership cannot be deactivated from this endpoint."
            )

        membership.is_active = False
        membership.save(update_fields=["is_active", "updated_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)
