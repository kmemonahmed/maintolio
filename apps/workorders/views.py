from django.db.models import Case, F, IntegerField, Value, When
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets, mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.organizations.models import OrganizationMembership
from apps.organizations.utils import get_current_membership
from apps.notifications.services import notify_work_order_status_changed

from .models import WorkOrder, WorkOrderUpdate

from .serializers import (
    AttachmentSerializer,
    ClientPortalWorkOrderCreateSerializer,
    ClientPortalWorkOrderRetrieveSerializer,
    WorkOrderAddUpdateSerializer,
    WorkOrderAssignSerializer,
    WorkOrderAttachmentUploadSerializer,
    WorkOrderChangeStatusSerializer,
    WorkOrderCreateUpdateSerializer,
    WorkOrderSerializer,
    WorkOrderUpdateSerializer,
    WorkOrderListSerializer,
    ClientPortalAddCommentSerializer,
    ClientPortalAttachmentUploadSerializer
)




MANAGE_WORK_ORDER_ROLES = [
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.MANAGER,
]

def _audit_value(value):
    if hasattr(value, "pk"):
        return value.pk

    return value


def _audit_values_equal(field, old_value, new_value):
    if field != "due_date":
        return old_value == new_value

    if old_value is None or new_value is None:
        return old_value is None and new_value is None

    if isinstance(new_value, str):
        parsed_value = parse_datetime(new_value)
        if parsed_value is not None:
            new_value = parsed_value

    return old_value == new_value


def _display_audit_value(field, value):
    if value in [None, ""]:
        return "empty"

    if field == "due_date":
        if isinstance(value, str):
            value = parse_datetime(value) or value

        if hasattr(value, "astimezone"):
            value = timezone.localtime(value)
            return value.strftime("%b %-d, %Y at %-I:%M %p")

    if field == "priority":
        return str(value).replace("_", " ").title()

    if field == "client":
        return getattr(value, "name", str(value))

    if field == "asset":
        return getattr(value, "name", str(value))

    if field == "requested_by_contact":
        return getattr(value, "full_name", str(value))

    if field == "description":
        text = str(value).strip()
        return text if len(text) <= 90 else f"{text[:87]}..."

    return str(value)


def _work_order_update_audit_message(changes):
    messages = []

    for field, old_value, new_value in changes:
        old_display = _display_audit_value(field, old_value)
        new_display = _display_audit_value(field, new_value)

        if field == "description":
            messages.append(
                f'Work order description updated from "{old_display}" to "{new_display}".'
            )
        elif field == "due_date":
            messages.append(
                f'Work order due date changed from {old_display} to {new_display}.'
            )
        elif field == "priority":
            messages.append(
                f"Work order priority changed from {old_display} to {new_display}."
            )
        elif field == "title":
            messages.append(
                f'Work order title changed from "{old_display}" to "{new_display}".'
            )
        elif field == "client":
            messages.append(
                f"Work order client changed from {old_display} to {new_display}."
            )
        elif field == "asset":
            messages.append(
                f"Work order asset changed from {old_display} to {new_display}."
            )
        elif field == "requested_by_contact":
            messages.append(
                f"Requested contact changed from {old_display} to {new_display}."
            )
        else:
            label = field.replace("_", " ")
            messages.append(
                f"Work order {label} changed from {old_display} to {new_display}."
            )

    return " ".join(messages)


def _attachment_audit_message(attachments):
    count = len(attachments)
    noun = "attachment" if count == 1 else "attachments"

    return f"Uploaded {count} {noun}."


class WorkOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = WorkOrder.objects.none()
    lookup_value_regex = "[0-9a-f-]{36}"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filterset_fields = ["status", "priority", "client", "asset", "assigned_to"]
    search_fields = [
        "title",
        "description",
        "client__name",
        "asset__name",
        "asset__serial_number",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "due_date",
        "priority",
        "status",
    ]

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WorkOrder.objects.none()

        current_membership = self.get_current_membership()

        queryset = WorkOrder.objects.filter(
            organization=current_membership.organization,
        )

        if self.action == "list":
            queryset = queryset.select_related(
                "asset",
                "assigned_to",
                "assigned_to__user",
            )
        else:
            queryset = queryset.select_related(
                "organization",
                "client",
                "asset",
                "created_by",
                "requested_by_contact",
                "assigned_to",
                "assigned_to__user",
            )

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["create", "partial_update", "update"]:
            return WorkOrderCreateUpdateSerializer

        if self.action == "list":
            return WorkOrderListSerializer

        return WorkOrderSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_membership"] = self.get_current_membership()
        return context

    def get_work_order_for_list_response(self, work_order):
        return (
            WorkOrder.objects
            .filter(
                organization=self.get_current_membership().organization,
                pk=work_order.pk,
            )
            .select_related(
                "asset",
                "assigned_to",
                "assigned_to__user",
            )
            .get()
        )

    def serialize_work_order_list(self, work_order):
        work_order = self.get_work_order_for_list_response(work_order)
        return WorkOrderListSerializer(work_order).data

    def require_work_order_manage_permission(self):
        current_membership = self.get_current_membership()

        if current_membership.role not in MANAGE_WORK_ORDER_ROLES:
            raise PermissionDenied(
                "You do not have permission to manage work orders."
            )

    @extend_schema(
        tags=["Work Orders"],
        summary="List work orders",
        responses=WorkOrderListSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        self.require_work_order_manage_permission()
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Work Orders"],
        summary="Retrieve work order",
        responses=WorkOrderSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        self.require_work_order_manage_permission()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Work Orders"],
        summary="Create work order",
        request=WorkOrderCreateUpdateSerializer,
        responses=WorkOrderListSerializer,
    )
    def create(self, request, *args, **kwargs):
        self.require_work_order_manage_permission()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_membership = self.get_current_membership()

        work_order = serializer.save(
            organization=current_membership.organization,
            created_by=request.user,
        )

        return Response(
            self.serialize_work_order_list(work_order),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Work Orders"],
        summary="Update work order",
        request=WorkOrderCreateUpdateSerializer,
        responses=WorkOrderSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        self.require_work_order_manage_permission()

        work_order = self.get_object()
        old_status = work_order.status

        serializer = self.get_serializer(
            work_order,
            data=request.data,
            partial=True,
        )
        original_values = {
            field: _audit_value(getattr(work_order, field))
            for field in serializer.fields
            if field in request.data
        }
        original_display_values = {
            field: getattr(work_order, field)
            for field in serializer.fields
            if field in request.data
        }
        serializer.is_valid(raise_exception=True)

        work_order = serializer.save()
        changes = []

        for field, old_value in original_values.items():
            if not _audit_values_equal(field, old_value, _audit_value(getattr(work_order, field))):
                changes.append(
                    (
                        field,
                        original_display_values[field],
                        getattr(work_order, field),
                    )
                )

        if changes:
            WorkOrderUpdate.objects.create(
                work_order=work_order,
                user=request.user,
                message=_work_order_update_audit_message(changes),
                old_status=old_status,
                new_status=work_order.status,
                is_internal=True,
            )

        return Response(
            WorkOrderSerializer(work_order).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Work Orders"],
        summary="Cancel work order",
        description="Soft-cancels a work order by setting its status to CANCELLED.",
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        self.require_work_order_manage_permission()

        work_order = self.get_object()

        if work_order.status == WorkOrder.Status.COMPLETED:
            raise PermissionDenied(
                "Completed work orders cannot be cancelled from this endpoint."
            )

        old_status = work_order.status
        work_order.status = WorkOrder.Status.CANCELLED
        work_order.save(update_fields=["status", "cancelled_at", "completed_at", "updated_at"])

        WorkOrderUpdate.objects.create(
            work_order=work_order,
            user=request.user,
            message="Work order cancelled.",
            old_status=old_status,
            new_status=WorkOrder.Status.CANCELLED,
            is_internal=True,
        )

        notify_work_order_status_changed(
            work_order,
            old_status,
            WorkOrder.Status.CANCELLED,
            actor=request.user,
            is_internal=False,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Work Orders"],
        summary="Assign technician",
        description="Assigns a technician to a work order and changes status to ASSIGNED.",
        request=WorkOrderAssignSerializer,
        responses=WorkOrderListSerializer,
    )
    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, *args, **kwargs):
        self.require_work_order_manage_permission()

        work_order = self.get_object()

        serializer = WorkOrderAssignSerializer(
            work_order,
            data=request.data,
            context={
                "request": request,
                "current_membership": self.get_current_membership(),
            },
        )
        serializer.is_valid(raise_exception=True)

        work_order = serializer.save()

        return Response(
            self.serialize_work_order_list(work_order),
            status=status.HTTP_200_OK,
        )

    def require_status_change_permission(self, work_order):
        current_membership = self.get_current_membership()

        if work_order.status == WorkOrder.Status.CANCELLED:
            if current_membership.role in MANAGE_WORK_ORDER_ROLES:
                return

            raise PermissionDenied(
                "Only workspace managers can reopen cancelled work orders."
            )

        if current_membership.role in MANAGE_WORK_ORDER_ROLES:
            return

        if current_membership.role == OrganizationMembership.Role.TECHNICIAN:
            if work_order.assigned_to_id == current_membership.id:
                return

        raise PermissionDenied(
            "You do not have permission to change this work order status."
        )

    @extend_schema(
        tags=["Work Orders"],
        summary="Change work order status",
        description="Changes work order status and creates a WorkOrderUpdate audit record.",
        request=WorkOrderChangeStatusSerializer,
        responses=WorkOrderListSerializer,
    )
    @action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, *args, **kwargs):
        work_order = self.get_object()

        self.require_status_change_permission(work_order)

        serializer = WorkOrderChangeStatusSerializer(
            work_order,
            data=request.data,
            context={
                "request": request,
                "current_membership": self.get_current_membership(),
            },
        )
        serializer.is_valid(raise_exception=True)

        work_order = serializer.save()

        return Response(
            self.serialize_work_order_list(work_order),
            status=status.HTTP_200_OK,
        )

    def require_add_update_permission(self, work_order):
        current_membership = self.get_current_membership()

        if current_membership.role in MANAGE_WORK_ORDER_ROLES:
            return

        if current_membership.role == OrganizationMembership.Role.TECHNICIAN:
            if work_order.assigned_to_id == current_membership.id:
                return

        raise PermissionDenied(
            "You do not have permission to add updates to this work order."
        )

    @extend_schema(
        tags=["Work Orders"],
        summary="Add work order update",
        description="Adds a comment/update to the work order without changing status.",
        request=WorkOrderAddUpdateSerializer,
        responses=WorkOrderUpdateSerializer,
    )
    @action(detail=True, methods=["post"], url_path="add-update")
    def add_update(self, request, *args, **kwargs):
        work_order = self.get_object()

        self.require_add_update_permission(work_order)

        serializer = WorkOrderAddUpdateSerializer(
            data=request.data,
            context={
                "request": request,
                "work_order": work_order,
                "current_membership": self.get_current_membership(),
            },
        )
        serializer.is_valid(raise_exception=True)

        update = serializer.save()

        response_serializer = WorkOrderUpdateSerializer(update)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )
    def require_attachment_upload_permission(self, work_order):
        if work_order.status in [
            WorkOrder.Status.COMPLETED,
            WorkOrder.Status.CANCELLED,
        ]:
            raise PermissionDenied(
                "Attachments cannot be uploaded to closed work orders."
            )

        current_membership = self.get_current_membership()

        if current_membership.role in MANAGE_WORK_ORDER_ROLES:
            return

        if current_membership.role == OrganizationMembership.Role.TECHNICIAN:
            if work_order.assigned_to_id == current_membership.id:
                return

        raise PermissionDenied(
            "You do not have permission to upload attachments to this work order."
        )

    @extend_schema(
        tags=["Work Orders"],
        summary="Upload work order attachment",
        description="Uploads one or more file attachments to a work order.",
        request=WorkOrderAttachmentUploadSerializer,
        responses=AttachmentSerializer(many=True),
    )
    @action(detail=True, methods=["post"], url_path="upload-attachment")
    def upload_attachment(self, request, *args, **kwargs):
        work_order = self.get_object()

        self.require_attachment_upload_permission(work_order)

        serializer = WorkOrderAttachmentUploadSerializer(
            data=request.data,
            context={
                "request": request,
                "work_order": work_order,
                "current_membership": self.get_current_membership(),
            },
        )
        serializer.is_valid(raise_exception=True)

        attachments = serializer.save()

        WorkOrderUpdate.objects.create(
            work_order=work_order,
            user=request.user,
            message=_attachment_audit_message(attachments),
            old_status=work_order.status,
            new_status=work_order.status,
            is_internal=True,
        )

        response_serializer = AttachmentSerializer(attachments, many=True)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def require_work_order_read_permission(self, work_order):
        current_membership = self.get_current_membership()

        if current_membership.role in MANAGE_WORK_ORDER_ROLES:
            return

        if current_membership.role == OrganizationMembership.Role.TECHNICIAN:
            if work_order.assigned_to_id == current_membership.id:
                return

        raise PermissionDenied(
            "You do not have permission to view this work order."
        )

    @extend_schema(
        tags=["Work Orders"],
        summary="List work order updates",
        description="Returns comments, notes, and status history for a work order.",
        responses=WorkOrderUpdateSerializer(many=True),
    )
    @action(detail=True, methods=["get"], url_path="updates")
    def updates(self, request, *args, **kwargs):
        work_order = self.get_object()

        self.require_work_order_read_permission(work_order)

        updates = (
            work_order.updates
            .select_related("user")
            .order_by("-created_at")
        )

        serializer = WorkOrderUpdateSerializer(updates, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Work Orders"],
        summary="List work order attachments",
        description="Returns files uploaded against a work order.",
        responses=AttachmentSerializer(many=True),
    )
    @action(detail=True, methods=["get"], url_path="attachments")
    def attachments(self, request, *args, **kwargs):
        work_order = self.get_object()

        self.require_work_order_read_permission(work_order)

        attachments = (
            work_order.attachments
            .select_related("uploaded_by")
            .order_by("-created_at")
        )

        serializer = AttachmentSerializer(
            attachments,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)



class TechnicianWorkOrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    queryset = WorkOrder.objects.none()
    lookup_value_regex = "[0-9a-f-]{36}"
    http_method_names = ["get", "head", "options"]
    filterset_fields = ["status", "priority", "client", "asset"]
    search_fields = [
        "title",
        "description",
        "client__name",
        "asset__name",
        "asset__serial_number",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "due_date",
        "priority",
        "status",
    ]

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WorkOrder.objects.none()

        current_membership = self.get_current_membership()

        if current_membership.role != OrganizationMembership.Role.TECHNICIAN:
            raise PermissionDenied(
                "Only technicians can access the technician work order portal."
            )

        queryset = WorkOrder.objects.filter(
            organization=current_membership.organization,
            assigned_to=current_membership,
        )

        if self.action == "list":
            queryset = queryset.select_related(
                "asset",
                "assigned_to",
                "assigned_to__user",
            )
        else:
            queryset = queryset.select_related(
                "organization",
                "client",
                "asset",
                "created_by",
                "requested_by_contact",
                "assigned_to",
                "assigned_to__user",
            )

        if self.action == "list" and "status" not in self.request.query_params:
            queryset = queryset.exclude(
                status__in=[
                    WorkOrder.Status.COMPLETED,
                    WorkOrder.Status.CANCELLED,
                ]
            )

        return queryset.annotate(
            technician_priority=Case(
                When(status=WorkOrder.Status.OVERDUE, then=Value(0)),
                When(status=WorkOrder.Status.IN_PROGRESS, then=Value(1)),
                When(status=WorkOrder.Status.ASSIGNED, then=Value(2)),
                When(status=WorkOrder.Status.ON_HOLD, then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by(
            "technician_priority",
            F("due_date").asc(nulls_last=True),
            "-updated_at",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return WorkOrderListSerializer

        return WorkOrderSerializer

    @extend_schema(
        tags=["Technician Portal"],
        summary="List assigned work orders",
        description="Returns work orders assigned to the logged-in technician.",
        responses=WorkOrderListSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Technician Portal"],
        summary="Retrieve assigned work order",
        description="Returns a single work order only if it is assigned to the logged-in technician.",
        responses=WorkOrderSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class ClientPortalWorkOrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    queryset = WorkOrder.objects.none()
    lookup_value_regex = "[0-9a-f-]{36}"
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["status", "priority", "asset"]
    search_fields = [
        "title",
        "description",
        "asset__name",
        "asset__serial_number",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "due_date",
        "priority",
        "status",
    ]

    def get_client_contact(self):
        if hasattr(self, "_client_contact"):
            return self._client_contact

        try:
            client_contact = self.request.user.client_contact_profile
        except Exception:
            raise PermissionDenied(
                "Only client contacts can access the client portal."
            )

        if not client_contact.is_active or not client_contact.can_login:
            raise PermissionDenied(
                "Your client portal access is inactive."
            )

        if not client_contact.client.is_active:
            raise PermissionDenied(
                "Your client account is inactive."
            )

        self._client_contact = client_contact
        return self._client_contact

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WorkOrder.objects.none()

        client_contact = self.get_client_contact()

        queryset = WorkOrder.objects.filter(client=client_contact.client)

        if self.action == "retrieve":
            queryset = queryset.select_related(
                "asset",
                "created_by",
                "requested_by_contact",
                "assigned_to",
                "assigned_to__user",
            )
        else:
            queryset = queryset.select_related(
                "organization",
                "client",
                "asset",
                "created_by",
                "requested_by_contact",
                "assigned_to",
                "assigned_to__user",
            )

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return ClientPortalWorkOrderCreateSerializer

        if self.action == "retrieve":
            return ClientPortalWorkOrderRetrieveSerializer

        return WorkOrderListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["client_contact"] = self.get_client_contact()
        return context

    @extend_schema(
        tags=["Client Portal"],
        summary="List client service requests",
        description="Returns work orders belonging to the logged-in client contact's client.",
        responses=WorkOrderListSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Client Portal"],
        summary="Create service request",
        description="Creates a work order for the logged-in client contact's client.",
        request=ClientPortalWorkOrderCreateSerializer,
        responses=WorkOrderListSerializer,
    )
    def create(self, request, *args, **kwargs):
        client_contact = self.get_client_contact()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        work_order = serializer.save(
            organization=client_contact.client.organization,
            client=client_contact.client,
            requested_by_contact=client_contact,
            created_by=request.user,
            status=WorkOrder.Status.OPEN,
        )

        response_serializer = WorkOrderListSerializer(work_order)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Client Portal"],
        summary="Retrieve client service request",
        description="Returns one work order only if it belongs to the logged-in client contact's client.",
        responses=ClientPortalWorkOrderRetrieveSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


    @extend_schema(
        tags=["Client Portal"],
        summary="Add comment to service request",
        description="Adds a public client comment to a service request. Internal notes are not allowed from client portal.",
        request=ClientPortalAddCommentSerializer,
        responses=WorkOrderUpdateSerializer,
    )
    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, *args, **kwargs):
        work_order = self.get_object()

        serializer = ClientPortalAddCommentSerializer(
            data=request.data,
            context={
                "request": request,
                "work_order": work_order,
                "client_contact": self.get_client_contact(),
            },
        )
        serializer.is_valid(raise_exception=True)

        update = serializer.save()

        response_serializer = WorkOrderUpdateSerializer(update)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Client Portal"],
        summary="Upload attachment to service request",
        description="Uploads one or more client-side attachments to a service request.",
        request=ClientPortalAttachmentUploadSerializer,
        responses=AttachmentSerializer(many=True),
    )
    @action(detail=True, methods=["post"], url_path="upload-attachment")
    def upload_attachment(self, request, *args, **kwargs):
        work_order = self.get_object()

        serializer = ClientPortalAttachmentUploadSerializer(
            data=request.data,
            context={
                "request": request,
                "work_order": work_order,
                "client_contact": self.get_client_contact(),
            },
        )
        serializer.is_valid(raise_exception=True)

        attachments = serializer.save()

        WorkOrderUpdate.objects.create(
            work_order=work_order,
            user=request.user,
            message=_attachment_audit_message(attachments),
            old_status=work_order.status,
            new_status=work_order.status,
            is_internal=False,
        )

        response_serializer = AttachmentSerializer(
            attachments,
            many=True,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Client Portal"],
        summary="List service request updates",
        description="Returns only public updates for a client service request. Internal notes are hidden.",
        responses=WorkOrderUpdateSerializer(many=True),
    )
    @action(detail=True, methods=["get"], url_path="updates")
    def updates(self, request, *args, **kwargs):
        work_order = self.get_object()

        updates = (
            work_order.updates
            .filter(is_internal=False)
            .select_related("user")
            .order_by("-created_at")
        )

        serializer = WorkOrderUpdateSerializer(updates, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


    @extend_schema(
        tags=["Client Portal"],
        summary="List service request attachments",
        description="Returns attachments uploaded to a client service request.",
        responses=AttachmentSerializer(many=True),
    )
    @action(detail=True, methods=["get"], url_path="attachments")
    def attachments(self, request, *args, **kwargs):
        work_order = self.get_object()

        attachments = (
            work_order.attachments
            .select_related("uploaded_by")
            .order_by("-created_at")
        )

        serializer = AttachmentSerializer(
            attachments,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
