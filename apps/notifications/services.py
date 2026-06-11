from apps.notifications.models import Notification
from apps.organizations.models import OrganizationMembership


def create_notification(user, title, message, organization=None, work_order=None):
    """Create one notification for a user."""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        organization=organization,
        work_order=work_order,
    )


def notify_work_order_overdue(work_order):
    """Notify the assigned technician and active organization leaders."""
    recipients_by_id = {}

    if work_order.assigned_to_id and work_order.assigned_to.user_id:
        recipients_by_id[work_order.assigned_to.user_id] = work_order.assigned_to.user

    leadership_memberships = OrganizationMembership.objects.filter(
        organization=work_order.organization,
        is_active=True,
        role__in=[
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.MANAGER,
        ],
    ).select_related("user")

    for membership in leadership_memberships:
        recipients_by_id[membership.user_id] = membership.user

    title = "Work order overdue"
    message = f'Work order "{work_order.title}" is now overdue.'

    notifications = [
        Notification(
            user=user,
            title=title,
            message=message,
            organization=work_order.organization,
            work_order=work_order,
        )
        for user in recipients_by_id.values()
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)

    return len(notifications)
