from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.test_helpers import (
    create_client,
    create_member_user,
    create_organization,
    create_work_order,
    paginated_results,
)
from apps.notifications.models import Notification
from apps.organizations.models import OrganizationMembership


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.organization = create_organization("Notification Org")
        self.user, _ = create_member_user(
            "notify-user@example.com",
            self.organization,
            OrganizationMembership.Role.OWNER,
        )
        self.other_user, _ = create_member_user(
            "notify-other@example.com",
            self.organization,
            OrganizationMembership.Role.OWNER,
        )
        self.client_record = create_client(self.organization, "Notification Client")
        self.work_order = create_work_order(
            self.organization,
            self.client_record,
            title="Notification work",
        )
        self.unread = Notification.objects.create(
            user=self.user,
            organization=self.organization,
            work_order=self.work_order,
            title="Unread notice",
            message="Needs attention.",
            is_read=False,
        )
        self.read = Notification.objects.create(
            user=self.user,
            organization=self.organization,
            work_order=self.work_order,
            title="Read notice",
            message="Already handled.",
            is_read=True,
        )
        self.other_notification = Notification.objects.create(
            user=self.other_user,
            organization=self.organization,
            work_order=self.work_order,
            title="Other user notice",
            message="Private.",
            is_read=False,
        )

    def test_notification_list_returns_only_request_user_notifications(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in paginated_results(response)}
        self.assertIn(str(self.unread.id), ids)
        self.assertIn(str(self.read.id), ids)
        self.assertNotIn(str(self.other_notification.id), ids)

    def test_mark_read_and_mark_unread_work(self):
        self.client.force_authenticate(user=self.user)

        read_response = self.client.post(f"/api/notifications/{self.unread.id}/mark-read/")
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.unread.refresh_from_db()
        self.assertTrue(self.unread.is_read)

        unread_response = self.client.post(f"/api/notifications/{self.unread.id}/mark-unread/")
        self.assertEqual(unread_response.status_code, status.HTTP_200_OK)
        self.unread.refresh_from_db()
        self.assertFalse(self.unread.is_read)

    def test_mark_all_read_and_unread_count_work(self):
        self.client.force_authenticate(user=self.user)

        count_response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(count_response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_response.data["unread_count"], 1)

        mark_all_response = self.client.post("/api/notifications/mark-all-read/")
        self.assertEqual(mark_all_response.status_code, status.HTTP_200_OK)
        self.assertEqual(mark_all_response.data["updated_count"], 1)

        count_response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(count_response.data["unread_count"], 0)
        self.other_notification.refresh_from_db()
        self.assertFalse(self.other_notification.is_read)

    def test_notifications_filter_by_is_read(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/?is_read=false")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in paginated_results(response)}
        self.assertEqual(ids, {str(self.unread.id)})
