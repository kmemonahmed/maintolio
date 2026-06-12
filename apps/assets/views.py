from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership
from apps.organizations.utils import get_current_membership

from .models import Asset
from .serializers import AssetCreateUpdateSerializer, AssetSerializer
from rest_framework.generics import ListAPIView
from apps.clients.models import Client


MANAGE_ASSET_ROLES = [
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.MANAGER,
]


class AssetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Asset.objects.none()
    lookup_value_regex = "[0-9a-f-]{36}"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filterset_fields = ["status", "client", "asset_type"]
    search_fields = [
        "name",
        "asset_type",
        "serial_number",
        "location",
        "client__name",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "name",
        "status",
    ]

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Asset.objects.none()

        current_membership = self.get_current_membership()

        return (
            Asset.objects
            .filter(client__organization=current_membership.organization)
            .select_related("client", "client__organization")
            .order_by("name")
        )

    def get_serializer_class(self):
        if self.action in ["create", "partial_update", "update"]:
            return AssetCreateUpdateSerializer

        return AssetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_membership"] = self.get_current_membership()
        return context

    def require_asset_manage_permission(self):
        current_membership = self.get_current_membership()

        if current_membership.role not in MANAGE_ASSET_ROLES:
            raise PermissionDenied(
                "You do not have permission to manage assets."
            )

    @extend_schema(
        tags=["Assets"],
        summary="List assets",
        responses=AssetSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.require_asset_manage_permission()
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Assets"],
        summary="Retrieve asset",
        responses=AssetSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        self.require_asset_manage_permission()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Assets"],
        summary="Create asset",
        request=AssetCreateUpdateSerializer,
        responses=AssetSerializer,
    )
    def create(self, request, *args, **kwargs):
        self.require_asset_manage_permission()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        asset = serializer.save()
        response_serializer = AssetSerializer(asset)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Assets"],
        summary="Update asset",
        request=AssetCreateUpdateSerializer,
        responses=AssetSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        self.require_asset_manage_permission()

        asset = self.get_object()

        serializer = self.get_serializer(
            asset,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        asset = serializer.save()
        response_serializer = AssetSerializer(asset)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Assets"],
        summary="Retire asset",
        description="Soft-deactivates an asset by setting its status to RETIRED.",
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        self.require_asset_manage_permission()

        asset = self.get_object()
        asset.status = Asset.Status.RETIRED
        asset.save(update_fields=["status", "updated_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientAssetListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Asset.objects.none()
    serializer_class = AssetSerializer

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    @extend_schema(
        tags=["Assets"],
        summary="List assets by client",
        description="Returns assets for a client only if the logged-in user is an active member of the client's organization.",
        responses=AssetSerializer(many=True),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Asset.objects.none()

        current_membership = self.get_current_membership()
        client_id = self.kwargs["client_id"]

        client = Client.objects.filter(
            id=client_id,
            organization=current_membership.organization,
            is_active=True,
        ).first()

        if not client:
            raise PermissionDenied(
                "You do not have access to this client's assets."
            )

        return (
            Asset.objects
            .filter(client=client)
            .select_related("client", "client__organization")
            .order_by("name")
        )
