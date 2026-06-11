from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.assets.models import Asset
from apps.clients.models import Client
from apps.notifications.models import Notification
from apps.organizations.models import OrganizationMembership
from apps.organizations.utils import get_current_membership
from apps.workorders.models import WorkOrder

from .serializers import (
    DailyWorkOrderSummarySerializer,
    DashboardSummarySerializer,
    WorkOrderSummarySerializer,
)


REPORT_VIEW_ROLES = [
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.MANAGER,
]


class BaseReportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_current_membership(self):
        if not hasattr(self, "_current_membership"):
            self._current_membership = get_current_membership(self.request)

        return self._current_membership

    def check_report_permission(self):
        current_membership = self.get_current_membership()

        if current_membership.role not in REPORT_VIEW_ROLES:
            raise PermissionDenied(
                "You do not have permission to view reports."
            )

        return current_membership

    def get_date_filters(self):
        date_from_raw = self.request.query_params.get("date_from")
        date_to_raw = self.request.query_params.get("date_to")

        date_from = None
        date_to = None

        if date_from_raw:
            date_from = parse_date(date_from_raw)

            if date_from is None:
                raise ValidationError(
                    {"date_from": "Invalid date format. Use YYYY-MM-DD."}
                )

        if date_to_raw:
            date_to = parse_date(date_to_raw)

            if date_to is None:
                raise ValidationError(
                    {"date_to": "Invalid date format. Use YYYY-MM-DD."}
                )

        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                {"date_to": "date_to must be greater than or equal to date_from."}
            )

        return date_from, date_to


class DashboardSummaryView(BaseReportView):
    serializer_class = DashboardSummarySerializer

    @extend_schema(
        tags=["Reports"],
        summary="Get dashboard summary",
        description="Returns organization-level dashboard summary counts for clients, assets, team members, work orders, priorities, overdue work, and unread notifications.",
        responses=DashboardSummarySerializer,
    )
    def get(self, request, *args, **kwargs):
        current_membership = self.check_report_permission()
        organization = current_membership.organization
        now = timezone.now()

        clients = Client.objects.filter(
            organization=organization,
            is_active=True,
        )

        assets = Asset.objects.filter(
            client__organization=organization,
        ).exclude(
            status=Asset.Status.RETIRED,
        )

        team_members = OrganizationMembership.objects.filter(
            organization=organization,
            is_active=True,
        )

        work_orders = WorkOrder.objects.filter(
            organization=organization,
        )

        active_work_orders = work_orders.exclude(
            status__in=[
                WorkOrder.Status.COMPLETED,
                WorkOrder.Status.CANCELLED,
            ]
        )

        data = {
            "total_clients": clients.count(),
            "total_assets": assets.count(),
            "total_team_members": team_members.count(),

            "total_work_orders": work_orders.count(),
            "open_work_orders": work_orders.filter(
                status=WorkOrder.Status.OPEN,
            ).count(),
            "assigned_work_orders": work_orders.filter(
                status=WorkOrder.Status.ASSIGNED,
            ).count(),
            "in_progress_work_orders": work_orders.filter(
                status=WorkOrder.Status.IN_PROGRESS,
            ).count(),
            "on_hold_work_orders": work_orders.filter(
                status=WorkOrder.Status.ON_HOLD,
            ).count(),
            "completed_work_orders": work_orders.filter(
                status=WorkOrder.Status.COMPLETED,
            ).count(),
            "cancelled_work_orders": work_orders.filter(
                status=WorkOrder.Status.CANCELLED,
            ).count(),

            "overdue_work_orders": active_work_orders.filter(
                due_date__lt=now,
            ).count(),

            "low_priority_work_orders": work_orders.filter(
                priority=WorkOrder.Priority.LOW,
            ).count(),
            "medium_priority_work_orders": work_orders.filter(
                priority=WorkOrder.Priority.MEDIUM,
            ).count(),
            "high_priority_work_orders": work_orders.filter(
                priority=WorkOrder.Priority.HIGH,
            ).count(),
            "urgent_priority_work_orders": work_orders.filter(
                priority=WorkOrder.Priority.URGENT,
            ).count(),

            "unread_notifications": Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count(),
        }

        serializer = self.get_serializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkOrderSummaryView(BaseReportView):
    serializer_class = WorkOrderSummarySerializer

    @extend_schema(
        tags=["Reports"],
        summary="Get work order summary",
        description="Returns work order summary grouped by status and priority. Optional filters: date_from and date_to using YYYY-MM-DD.",
        parameters=[
            OpenApiParameter(
                name="date_from",
                description="Filter work orders created on or after this date. Format: YYYY-MM-DD.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="date_to",
                description="Filter work orders created on or before this date. Format: YYYY-MM-DD.",
                required=False,
                type=str,
            ),
        ],
        responses=WorkOrderSummarySerializer,
    )
    def get(self, request, *args, **kwargs):
        current_membership = self.check_report_permission()
        organization = current_membership.organization

        date_from, date_to = self.get_date_filters()

        work_orders = WorkOrder.objects.filter(
            organization=organization,
        )

        if date_from:
            work_orders = work_orders.filter(created_at__date__gte=date_from)

        if date_to:
            work_orders = work_orders.filter(created_at__date__lte=date_to)

        now = timezone.now()
        today = timezone.localdate()

        active_work_orders = work_orders.exclude(
            status__in=[
                WorkOrder.Status.COMPLETED,
                WorkOrder.Status.CANCELLED,
            ]
        )

        status_breakdown = {
            status_value: work_orders.filter(status=status_value).count()
            for status_value, _ in WorkOrder.Status.choices
        }

        priority_breakdown = {
            priority_value: work_orders.filter(priority=priority_value).count()
            for priority_value, _ in WorkOrder.Priority.choices
        }

        data = {
            "date_from": date_from,
            "date_to": date_to,

            "total_work_orders": work_orders.count(),
            "assigned_work_orders": work_orders.filter(
                assigned_to__isnull=False,
            ).count(),
            "unassigned_work_orders": work_orders.filter(
                assigned_to__isnull=True,
            ).count(),

            "overdue_work_orders": active_work_orders.filter(
                due_date__lt=now,
            ).count(),
            "due_today_work_orders": active_work_orders.filter(
                due_date__date=today,
            ).count(),

            "status_breakdown": status_breakdown,
            "priority_breakdown": priority_breakdown,
        }

        serializer = self.get_serializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)


class DailyWorkOrderSummaryView(BaseReportView):
    serializer_class = DailyWorkOrderSummarySerializer

    @extend_schema(
        tags=["Reports"],
        summary="Get daily work order summary",
        description="Returns daily work order counts grouped by created date. Optional filters: date_from and date_to using YYYY-MM-DD.",
        parameters=[
            OpenApiParameter(
                name="date_from",
                description="Filter work orders created on or after this date. Format: YYYY-MM-DD.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="date_to",
                description="Filter work orders created on or before this date. Format: YYYY-MM-DD.",
                required=False,
                type=str,
            ),
        ],
        responses=DailyWorkOrderSummarySerializer,
    )
    def get(self, request, *args, **kwargs):
        current_membership = self.check_report_permission()
        organization = current_membership.organization

        date_from, date_to = self.get_date_filters()

        work_orders = WorkOrder.objects.filter(
            organization=organization,
        )

        if date_from:
            work_orders = work_orders.filter(created_at__date__gte=date_from)

        if date_to:
            work_orders = work_orders.filter(created_at__date__lte=date_to)

        daily_rows = (
            work_orders
            .annotate(report_date=TruncDate("created_at"))
            .values("report_date")
            .annotate(
                total_work_orders=Count("id"),

                open_work_orders=Count(
                    "id",
                    filter=Q(status=WorkOrder.Status.OPEN),
                ),
                assigned_work_orders=Count(
                    "id",
                    filter=Q(status=WorkOrder.Status.ASSIGNED),
                ),
                in_progress_work_orders=Count(
                    "id",
                    filter=Q(status=WorkOrder.Status.IN_PROGRESS),
                ),
                on_hold_work_orders=Count(
                    "id",
                    filter=Q(status=WorkOrder.Status.ON_HOLD),
                ),
                completed_work_orders=Count(
                    "id",
                    filter=Q(status=WorkOrder.Status.COMPLETED),
                ),
                cancelled_work_orders=Count(
                    "id",
                    filter=Q(status=WorkOrder.Status.CANCELLED),
                ),

                low_priority_work_orders=Count(
                    "id",
                    filter=Q(priority=WorkOrder.Priority.LOW),
                ),
                medium_priority_work_orders=Count(
                    "id",
                    filter=Q(priority=WorkOrder.Priority.MEDIUM),
                ),
                high_priority_work_orders=Count(
                    "id",
                    filter=Q(priority=WorkOrder.Priority.HIGH),
                ),
                urgent_priority_work_orders=Count(
                    "id",
                    filter=Q(priority=WorkOrder.Priority.URGENT),
                ),
            )
            .order_by("-report_date")
        )

        results = []

        for row in daily_rows:
            results.append(
                {
                    "date": row["report_date"],
                    "total_work_orders": row["total_work_orders"],

                    "open_work_orders": row["open_work_orders"],
                    "assigned_work_orders": row["assigned_work_orders"],
                    "in_progress_work_orders": row["in_progress_work_orders"],
                    "on_hold_work_orders": row["on_hold_work_orders"],
                    "completed_work_orders": row["completed_work_orders"],
                    "cancelled_work_orders": row["cancelled_work_orders"],

                    "low_priority_work_orders": row["low_priority_work_orders"],
                    "medium_priority_work_orders": row["medium_priority_work_orders"],
                    "high_priority_work_orders": row["high_priority_work_orders"],
                    "urgent_priority_work_orders": row["urgent_priority_work_orders"],
                }
            )

        data = {
            "date_from": date_from,
            "date_to": date_to,
            "results": results,
        }

        serializer = self.get_serializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)