from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.notifications.services import notify_work_order_overdue
from apps.workorders.models import WorkOrder, WorkOrderUpdate


@shared_task
def debug_task():
    return "Celery is working"


@shared_task
def mark_overdue_work_orders():
    """Mark due work orders overdue while preserving update history."""
    overdue_candidates = WorkOrder.objects.filter(
        due_date__isnull=False,
        due_date__lt=timezone.now(),
    ).exclude(
        status__in=[
            WorkOrder.Status.COMPLETED,
            WorkOrder.Status.CANCELLED,
            WorkOrder.Status.OVERDUE,
        ]
    ).select_related("organization", "assigned_to__user")

    updated_count = 0

    for work_order in overdue_candidates.iterator():
        old_status = work_order.status

        with transaction.atomic():
            work_order.status = WorkOrder.Status.OVERDUE
            work_order.save(update_fields=["status", "updated_at"])

            WorkOrderUpdate.objects.create(
                work_order=work_order,
                user=None,
                old_status=old_status,
                new_status=WorkOrder.Status.OVERDUE,
                message="Work order automatically marked as overdue.",
                is_internal=True,
            )

        notify_work_order_overdue(work_order)
        updated_count += 1

    return {"updated_count": updated_count}
