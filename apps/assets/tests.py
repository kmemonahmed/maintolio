from rest_framework import status
from rest_framework.test import APITestCase

from apps.assets.models import Asset
from apps.core.test_helpers import (
    create_asset,
    create_client,
    create_member_user,
    create_organization,
    paginated_results,
)
from apps.organizations.models import OrganizationMembership


class AssetTenantIsolationTests(APITestCase):
    def setUp(self):
        self.org_a = create_organization("Assets Org A")
        self.org_b = create_organization("Assets Org B")
        self.user_a, _ = create_member_user(
            "assets-a@example.com",
            self.org_a,
            OrganizationMembership.Role.OWNER,
        )
        self.user_b, _ = create_member_user(
            "assets-b@example.com",
            self.org_b,
            OrganizationMembership.Role.OWNER,
        )
        self.client_a = create_client(self.org_a, "Asset Client A")
        self.client_b = create_client(self.org_b, "Asset Client B")
        self.asset_a = create_asset(
            self.client_a,
            name="Main Compressor",
            serial_number="A-SN-001",
            asset_type="Compressor",
        )
        self.asset_b = create_asset(
            self.client_b,
            name="Remote Pump",
            serial_number="B-SN-001",
            asset_type="Pump",
        )

    def test_asset_list_retrieve_update_delete_are_tenant_scoped(self):
        self.client.force_authenticate(user=self.user_a)

        list_response = self.client.get("/api/assets/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in paginated_results(list_response)}
        self.assertIn(str(self.asset_a.id), ids)
        self.assertNotIn(str(self.asset_b.id), ids)

        retrieve_response = self.client.get(f"/api/assets/{self.asset_b.id}/")
        self.assertEqual(retrieve_response.status_code, status.HTTP_404_NOT_FOUND)

        update_response = self.client.patch(
            f"/api/assets/{self.asset_b.id}/",
            {"name": "Should Not Update"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)

        delete_response = self.client.delete(f"/api/assets/{self.asset_b.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        self.asset_b.refresh_from_db()
        self.assertEqual(self.asset_b.status, Asset.Status.ACTIVE)

    def test_asset_create_rejects_other_tenant_client(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/assets/",
            {
                "client": str(self.client_b.id),
                "name": "Wrong Tenant Asset",
                "asset_type": "Pump",
                "serial_number": "WRONG-SN",
                "location": "Elsewhere",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Asset.objects.filter(serial_number="WRONG-SN").exists())

    def test_asset_search_by_name_and_serial_number(self):
        self.client.force_authenticate(user=self.user_a)

        by_name = self.client.get("/api/assets/?search=Compressor")
        by_serial = self.client.get("/api/assets/?search=A-SN-001")

        self.assertEqual(by_name.status_code, status.HTTP_200_OK)
        self.assertEqual(by_serial.status_code, status.HTTP_200_OK)
        self.assertEqual(paginated_results(by_name)[0]["id"], str(self.asset_a.id))
        self.assertEqual(paginated_results(by_serial)[0]["id"], str(self.asset_a.id))
