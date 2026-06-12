from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.assets.models import Asset
from apps.clients.models import Client, ClientContact
from apps.organizations.models import Organization, OrganizationMembership
from apps.workorders.models import WorkOrder


TEST_PASSWORD = "Str0ngPass!234"


def create_user(email, full_name="Test User", password=TEST_PASSWORD, **kwargs):
    return get_user_model().objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        phone=kwargs.pop("phone", ""),
        **kwargs,
    )


def create_organization(name="Test Organization", **kwargs):
    return Organization.objects.create(name=name, **kwargs)


def create_membership(user, organization, role=OrganizationMembership.Role.OWNER, **kwargs):
    return OrganizationMembership.objects.create(
        user=user,
        organization=organization,
        role=role,
        is_active=kwargs.pop("is_active", True),
        **kwargs,
    )


def create_member_user(
    email,
    organization,
    role=OrganizationMembership.Role.OWNER,
    full_name="Member User",
):
    user = create_user(email=email, full_name=full_name)
    membership = create_membership(user=user, organization=organization, role=role)
    return user, membership


def create_client(organization, name="Client Co", **kwargs):
    return Client.objects.create(
        organization=organization,
        name=name,
        email=kwargs.pop("email", f"{name.lower().replace(' ', '')}@example.com"),
        phone=kwargs.pop("phone", "1234567890"),
        industry=kwargs.pop("industry", "Manufacturing"),
        **kwargs,
    )


def create_client_contact(
    client,
    email="contact@example.com",
    full_name="Client Contact",
    can_login=False,
    password=TEST_PASSWORD,
    **kwargs,
):
    user = None

    if can_login:
        user = create_user(email=email, full_name=full_name, password=password)

    return ClientContact.objects.create(
        client=client,
        user=user,
        full_name=full_name,
        email=email,
        phone=kwargs.pop("phone", "1234567890"),
        position=kwargs.pop("position", "Operations"),
        can_login=can_login,
        is_active=kwargs.pop("is_active", True),
        **kwargs,
    )


def create_asset(client, name="Boiler", serial_number="SN-001", **kwargs):
    return Asset.objects.create(
        client=client,
        name=name,
        asset_type=kwargs.pop("asset_type", "HVAC"),
        serial_number=serial_number,
        location=kwargs.pop("location", "Main Floor"),
        status=kwargs.pop("status", Asset.Status.ACTIVE),
        **kwargs,
    )


def create_work_order(
    organization,
    client,
    title="Leaking pump",
    asset=None,
    created_by=None,
    requested_by_contact=None,
    assigned_to=None,
    **kwargs,
):
    return WorkOrder.objects.create(
        organization=organization,
        client=client,
        asset=asset,
        title=title,
        description=kwargs.pop("description", "Investigate and repair."),
        priority=kwargs.pop("priority", WorkOrder.Priority.MEDIUM),
        status=kwargs.pop("status", WorkOrder.Status.OPEN),
        created_by=created_by,
        requested_by_contact=requested_by_contact,
        assigned_to=assigned_to,
        due_date=kwargs.pop("due_date", timezone.now() + timezone.timedelta(days=1)),
        **kwargs,
    )


def paginated_results(response):
    data = response.data

    if isinstance(data, dict) and "results" in data:
        return data["results"]

    return data
