from rest_framework.exceptions import PermissionDenied

from apps.organizations.models import OrganizationMembership


def get_current_membership(request):
    """
    Resolve the current organization membership for the logged-in user.

    V1 behavior:
    - If user has one active organization membership, use that.
    - If user has multiple active memberships, allow X-Organization-ID header.
    """

    user = request.user

    memberships = (
        OrganizationMembership.objects
        .filter(user=user, is_active=True, organization__is_active=True)
        .select_related("organization", "user")
    )

    organization_id = request.headers.get("X-Organization-ID")

    if organization_id:
        membership = memberships.filter(organization_id=organization_id).first()

        if not membership:
            raise PermissionDenied(
                "You do not have access to this organization."
            )

        return membership

    membership_count = memberships.count()

    if membership_count == 0:
        raise PermissionDenied(
            "You are not a member of any active organization."
        )

    if membership_count > 1:
        raise PermissionDenied(
            "Multiple organizations found. Please provide X-Organization-ID header."
        )

    return memberships.first()


def is_owner_or_admin(membership):
    return membership.role in [
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
    ]