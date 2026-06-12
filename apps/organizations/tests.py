from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.test_helpers import (
    TEST_PASSWORD,
    create_member_user,
    create_organization,
)
from apps.organizations.models import OrganizationMembership


class TeamMemberAPITests(APITestCase):
    def setUp(self):
        self.organization = create_organization("Team Org")
        self.owner, self.owner_membership = create_member_user(
            "owner-team@example.com",
            self.organization,
            OrganizationMembership.Role.OWNER,
            "Owner User",
        )
        self.admin, self.admin_membership = create_member_user(
            "admin-team@example.com",
            self.organization,
            OrganizationMembership.Role.ADMIN,
            "Admin User",
        )
        self.manager, self.manager_membership = create_member_user(
            "manager-team@example.com",
            self.organization,
            OrganizationMembership.Role.MANAGER,
            "Manager User",
        )
        self.technician, self.technician_membership = create_member_user(
            "tech-team@example.com",
            self.organization,
            OrganizationMembership.Role.TECHNICIAN,
            "Technician User",
        )
        self.url = "/api/team-members/"

    def test_owner_and_admin_can_create_team_member(self):
        payload = {
            "full_name": "New Technician",
            "email": "new-tech@example.com",
            "role": OrganizationMembership.Role.TECHNICIAN,
            "password": TEST_PASSWORD,
        }

        self.client.force_authenticate(user=self.owner)
        owner_response = self.client.post(self.url, payload, format="json")
        self.assertEqual(owner_response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.admin)
        admin_response = self.client.post(
            self.url,
            {
                "full_name": "New Manager",
                "email": "new-manager@example.com",
                "role": OrganizationMembership.Role.MANAGER,
                "password": TEST_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(admin_response.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_create_team_member(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            self.url,
            {
                "full_name": "Blocked User",
                "email": "blocked@example.com",
                "role": OrganizationMembership.Role.TECHNICIAN,
                "password": TEST_PASSWORD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_cannot_access_team_member_management(self):
        self.client.force_authenticate(user=self.technician)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleting_team_member_soft_deactivates_membership(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f"{self.url}{self.admin_membership.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.admin_membership.refresh_from_db()
        self.assertFalse(self.admin_membership.is_active)
