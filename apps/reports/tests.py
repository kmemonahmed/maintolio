from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.test_helpers import (
    create_client,
    create_member_user,
    create_organization,
    create_work_order,
)
from apps.notifications.models import Notification
from apps.organizations.models import OrganizationMembership
from apps.reports.models import DailyWorkOrderSummary
from apps.reports.tasks import generate_daily_work_order_summaries
from apps.workorders.models import WorkOrder, WorkOrderUpdate
from apps.workorders.tasks import mark_overdue_work_orders


class ReportsAPITests(APITestCase):
    def setUp(self):
        self.org_a = create_organization("Reports Org A")
        self.org_b = create_organization("Reports Org B")
        self.owner, _ = create_member_user(
            "reports-owner@example.com",
            self.org_a,
            OrganizationMembership.Role.OWNER,
        )
        self.admin, _ = create_member_user(
            "reports-admin@example.com",
            self.org_a,
            OrganizationMembership.Role.ADMIN,
        )
        self.manager, _ = create_member_user(
            "reports-manager@example.com",
            self.org_a,
            OrganizationMembership.Role.MANAGER,
        )
        self.technician, _ = create_member_user(
            "reports-tech@example.com",
            self.org_a,
            OrganizationMembership.Role.TECHNICIAN,
        )
        self.client_a = create_client(self.org_a, "Reports Client A")
        self.client_b = create_client(self.org_b, "Reports Client B")
        create_work_order(
            self.org_a,
            self.client_a,
            title="Reports Open",
            status=WorkOrder.Status.OPEN,
            priority=WorkOrder.Priority.URGENT,
        )
        create_work_order(
            self.org_b,
            self.client_b,
            title="Reports Other Org",
            status=WorkOrder.Status.OPEN,
        )

    def test_owner_admin_manager_can_access_dashboard_summary(self):
        for user in [self.owner, self.admin, self.manager]:
            self.client.force_authenticate(user=user)
            response = self.client.get("/api/reports/dashboard-summary/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_technician_cannot_access_reports(self):
        self.client.force_authenticate(user=self.technician)

        response = self.client.get("/api/reports/dashboard-summary/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_summary_is_organization_scoped(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.get("/api/reports/dashboard-summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_clients"], 1)
        self.assertEqual(response.data["total_work_orders"], 1)

    def test_work_order_summary_returns_counts(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.get("/api/reports/work-order-summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_work_orders"], 1)
        self.assertEqual(response.data["priority_breakdown"][WorkOrder.Priority.URGENT], 1)

    def test_daily_work_order_summary_returns_results_safely(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.get("/api/reports/daily-work-order-summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)


class BackgroundTaskTests(APITestCase):
    def setUp(self):
        self.organization = create_organization("Task Org")
        self.owner, self.owner_membership = create_member_user(
            "task-owner@example.com",
            self.organization,
            OrganizationMembership.Role.OWNER,
        )
        self.tech, self.tech_membership = create_member_user(
            "task-tech@example.com",
            self.organization,
            OrganizationMembership.Role.TECHNICIAN,
        )
        self.client_record = create_client(self.organization, "Task Client")

    def test_mark_overdue_work_orders_updates_status_audit_and_notifications(self):
        work_order = create_work_order(
            self.organization,
            self.client_record,
            title="Old due work",
            status=WorkOrder.Status.IN_PROGRESS,
            assigned_to=self.tech_membership,
            due_date=timezone.now() - timezone.timedelta(days=2),
        )

        result = mark_overdue_work_orders()

        self.assertEqual(result["updated_count"], 1)
        work_order.refresh_from_db()
        self.assertEqual(work_order.status, WorkOrder.Status.OVERDUE)
        self.assertTrue(
            WorkOrderUpdate.objects.filter(
                work_order=work_order,
                new_status=WorkOrder.Status.OVERDUE,
                user__isnull=True,
            ).exists()
        )
        self.assertGreaterEqual(Notification.objects.filter(work_order=work_order).count(), 1)

    def test_generate_daily_work_order_summaries_upserts_summary(self):
        today = timezone.localdate()
        create_work_order(
            self.organization,
            self.client_record,
            title="Today urgent work",
            status=WorkOrder.Status.OPEN,
            priority=WorkOrder.Priority.URGENT,
        )

        result = generate_daily_work_order_summaries(today.isoformat())
        generate_daily_work_order_summaries(today.isoformat())

        self.assertEqual(result["date"], today.isoformat())
        summary = DailyWorkOrderSummary.objects.get(
            organization=self.organization,
            date=today,
        )
        self.assertEqual(summary.total_work_orders, 1)
        self.assertEqual(summary.open_work_orders, 1)
        self.assertEqual(summary.urgent_work_orders, 1)
        self.assertEqual(
            DailyWorkOrderSummary.objects.filter(
                organization=self.organization,
                date=today,
            ).count(),
            1,
        )
