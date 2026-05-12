from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership
from apps.organizations.utils import get_current_membership

from .models import Client, ClientContact
from .serializers import (
    ClientCreateUpdateSerializer,
    ClientSerializer,
    ClientContactSerializer,
    ClientContactCreateSerializer,
    ClientContactUpdateSerializer
)


MANAGE_CLIENT_ROLES = [
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.MANAGER,
]


class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    def get_queryset(self):
        current_membership = self.get_current_membership()

        return (
            Client.objects
            .filter(organization=current_membership.organization)
            .order_by("name")
        )

    def get_serializer_class(self):
        if self.action in ["create", "partial_update", "update"]:
            return ClientCreateUpdateSerializer

        return ClientSerializer

    def require_client_manage_permission(self):
        current_membership = self.get_current_membership()

        if current_membership.role not in MANAGE_CLIENT_ROLES:
            raise PermissionDenied(
                "You do not have permission to manage clients."
            )

    @extend_schema(
        tags=["Clients"],
        summary="List clients",
        responses=ClientSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.require_client_manage_permission()
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Clients"],
        summary="Retrieve client",
        responses=ClientSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        self.require_client_manage_permission()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Clients"],
        summary="Create client",
        request=ClientCreateUpdateSerializer,
        responses=ClientSerializer,
    )
    def create(self, request, *args, **kwargs):
        self.require_client_manage_permission()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_membership = self.get_current_membership()

        client = serializer.save(
            organization=current_membership.organization
        )

        response_serializer = ClientSerializer(client)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Clients"],
        summary="Update client",
        request=ClientCreateUpdateSerializer,
        responses=ClientSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        self.require_client_manage_permission()

        client = self.get_object()

        serializer = self.get_serializer(
            client,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        client = serializer.save()

        response_serializer = ClientSerializer(client)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Clients"],
        summary="Deactivate client",
        description="Soft-deactivates a client instead of deleting it.",
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        self.require_client_manage_permission()

        client = self.get_object()
        client.is_active = False
        client.save(update_fields=["is_active", "updated_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientContactViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    def get_queryset(self):
        current_membership = self.get_current_membership()

        return (
            ClientContact.objects
            .filter(client__organization=current_membership.organization)
            .select_related("client", "client__organization", "user")
            .order_by("client__name", "full_name")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ClientContactCreateSerializer

        if self.action in ["partial_update", "update"]:
            return ClientContactUpdateSerializer

        return ClientContactSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_membership"] = self.get_current_membership()
        return context

    def require_client_contact_manage_permission(self):
        current_membership = self.get_current_membership()

        if current_membership.role not in MANAGE_CLIENT_ROLES:
            raise PermissionDenied(
                "You do not have permission to manage client contacts."
            )

    @extend_schema(
        tags=["Client Contacts"],
        summary="List client contacts",
        responses=ClientContactSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.require_client_contact_manage_permission()
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Client Contacts"],
        summary="Retrieve client contact",
        responses=ClientContactSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        self.require_client_contact_manage_permission()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Client Contacts"],
        summary="Create client contact",
        request=ClientContactCreateSerializer,
        responses=ClientContactSerializer,
    )
    def create(self, request, *args, **kwargs):
        self.require_client_contact_manage_permission()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_contact = serializer.save()
        response_serializer = ClientContactSerializer(client_contact)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Client Contacts"],
        summary="Update client contact",
        request=ClientContactUpdateSerializer,
        responses=ClientContactSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        self.require_client_contact_manage_permission()

        client_contact = self.get_object()

        serializer = self.get_serializer(
            client_contact,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        client_contact = serializer.save()
        response_serializer = ClientContactSerializer(client_contact)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Client Contacts"],
        summary="Deactivate client contact",
        description="Soft-deactivates a client contact instead of deleting it.",
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        self.require_client_contact_manage_permission()

        client_contact = self.get_object()
        client_contact.is_active = False
        client_contact.save(update_fields=["is_active", "updated_at"])

        return Response(status=status.HTTP_204_NO_CONTENT)