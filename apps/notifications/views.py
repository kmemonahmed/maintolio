from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.none()
    lookup_value_regex = "[0-9a-f-]{36}"
    serializer_class = NotificationSerializer
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["is_read", "organization", "work_order"]
    search_fields = [
        "title",
        "message",
        "work_order__title",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "is_read",
    ]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        queryset = (
            Notification.objects
            .filter(user=self.request.user)
            .select_related("organization", "work_order")
            .order_by("-created_at")
        )

        is_read = self.request.query_params.get("is_read")

        if is_read == "true":
            queryset = queryset.filter(is_read=True)

        if is_read == "false":
            queryset = queryset.filter(is_read=False)

        return queryset

    @extend_schema(
        tags=["Notifications"],
        summary="List notifications",
        description="Returns notifications for the logged-in user only. Optional filter: ?is_read=true or ?is_read=false.",
        responses=NotificationSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Notifications"],
        summary="Retrieve notification",
        description="Returns one notification if it belongs to the logged-in user.",
        responses=NotificationSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Notifications"],
        summary="Mark notification as read",
        responses=NotificationSerializer,
    )
    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])

        serializer = self.get_serializer(notification)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Notifications"],
        summary="Mark notification as unread",
        responses=NotificationSerializer,
    )
    @action(detail=True, methods=["post"], url_path="mark-unread")
    def mark_unread(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = False
        notification.save(update_fields=["is_read", "updated_at"])

        serializer = self.get_serializer(notification)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Notifications"],
        summary="Mark all notifications as read",
        responses={200: dict},
    )
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request, *args, **kwargs):
        updated_count = (
            Notification.objects
            .filter(user=request.user, is_read=False)
            .update(is_read=True)
        )

        return Response(
            {
                "message": "All notifications marked as read.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Notifications"],
        summary="Get unread notification count",
        responses={200: dict},
    )
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request, *args, **kwargs):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()

        return Response(
            {"unread_count": count},
            status=status.HTTP_200_OK,
        )
