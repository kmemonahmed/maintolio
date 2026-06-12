from rest_framework import status
from rest_framework.test import APITestCase

from apps.clients.models import Client, ClientContact
from apps.core.test_helpers import (
    TEST_PASSWORD,
    create_client,
    create_client_contact,
    create_member_user,
    create_organization,
    paginated_results,
)
from apps.organizations.models import OrganizationMembership


class ClientTenantIsolationTests(APITestCase):
    def setUp(self):
        self.org_a = create_organization("Clients Org A")
        self.org_b = create_organization("Clients Org B")
        self.user_a, _ = create_member_user(
            "clients-a@example.com",
            self.org_a,
            OrganizationMembership.Role.OWNER,
        )
        self.user_b, _ = create_member_user(
            "clients-b@example.com",
            self.org_b,
            OrganizationMembership.Role.OWNER,
        )
        self.client_a = create_client(self.org_a, "A Client")
        self.client_b = create_client(self.org_b, "B Client")
        self.contact_a = create_client_contact(
            self.client_a,
            email="contact-a@example.com",
            full_name="Contact A",
        )
        self.contact_b = create_client_contact(
            self.client_b,
            email="contact-b@example.com",
            full_name="Contact B",
        )

    def test_client_list_retrieve_update_delete_are_tenant_scoped(self):
        self.client.force_authenticate(user=self.user_a)

        list_response = self.client.get("/api/clients/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in paginated_results(list_response)}
        self.assertIn(str(self.client_a.id), ids)
        self.assertNotIn(str(self.client_b.id), ids)

        retrieve_response = self.client.get(f"/api/clients/{self.client_b.id}/")
        self.assertEqual(retrieve_response.status_code, status.HTTP_404_NOT_FOUND)

        update_response = self.client.patch(
            f"/api/clients/{self.client_b.id}/",
            {"name": "Should Not Update"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)

        delete_response = self.client.delete(f"/api/clients/{self.client_b.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        self.client_b.refresh_from_db()
        self.assertTrue(self.client_b.is_active)

    def test_client_contact_list_retrieve_update_delete_are_tenant_scoped(self):
        self.client.force_authenticate(user=self.user_a)

        list_response = self.client.get("/api/client-contacts/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in paginated_results(list_response)}
        self.assertIn(str(self.contact_a.id), ids)
        self.assertNotIn(str(self.contact_b.id), ids)

        retrieve_response = self.client.get(f"/api/client-contacts/{self.contact_b.id}/")
        self.assertEqual(retrieve_response.status_code, status.HTTP_404_NOT_FOUND)

        update_response = self.client.patch(
            f"/api/client-contacts/{self.contact_b.id}/",
            {"full_name": "Should Not Update"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)

        delete_response = self.client.delete(f"/api/client-contacts/{self.contact_b.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        self.contact_b.refresh_from_db()
        self.assertTrue(self.contact_b.is_active)

    def test_client_contact_create_rejects_other_tenant_client(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            "/api/client-contacts/",
            {
                "client": str(self.client_b.id),
                "full_name": "Wrong Tenant",
                "email": "wrong-tenant@example.com",
                "can_login": True,
                "password": TEST_PASSWORD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ClientContact.objects.filter(email="wrong-tenant@example.com").exists())

    def test_client_filters_search_and_pagination_shape(self):
        create_client(self.org_a, "Inactive Client", is_active=False, industry="Healthcare")
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get("/api/clients/?is_active=true&search=A Client")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["results"][0]["id"], str(self.client_a.id))
        self.assertEqual(Client.objects.filter(organization=self.org_a).count(), 2)
