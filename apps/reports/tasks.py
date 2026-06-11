from datetime import date

from celery import shared_task
from django.utils import timezone

from apps.organizations.models import Organization
from apps.reports.models import DailyWorkOrderSummary
from apps.workorders.models import WorkOrder


def _parse_target_date(target_date):
    if target_date is None:
        return timezone.localdate()

    if isinstance(target_date, date):
        return target_date

    return date.fromisoformat(target_date)


@shared_task
def generate_daily_work_order_summaries(target_date=None):
    """Upsert daily per-organization work order metrics."""
    summary_date = _parse_target_date(target_date)
    organizations_processed = 0

    for organization in Organization.objects.iterator():
        work_orders = WorkOrder.objects.filter(
            organization=organization,
            created_at__date=summary_date,
        )

        DailyWorkOrderSummary.objects.update_or_create(
            organization=organization,
            date=summary_date,
            defaults={
                "total_work_orders": work_orders.count(),
                "open_work_orders": work_orders.filter(status=WorkOrder.Status.OPEN).count(),
                "assigned_work_orders": work_orders.filter(status=WorkOrder.Status.ASSIGNED).count(),
                "in_progress_work_orders": work_orders.filter(status=WorkOrder.Status.IN_PROGRESS).count(),
                "on_hold_work_orders": work_orders.filter(status=WorkOrder.Status.ON_HOLD).count(),
                "completed_work_orders": work_orders.filter(status=WorkOrder.Status.COMPLETED).count(),
                "cancelled_work_orders": work_orders.filter(status=WorkOrder.Status.CANCELLED).count(),
                "overdue_work_orders": work_orders.filter(status=WorkOrder.Status.OVERDUE).count(),
                "urgent_work_orders": work_orders.filter(priority=WorkOrder.Priority.URGENT).count(),
            },
        )
        organizations_processed += 1

    return {
        "date": summary_date.isoformat(),
        "organizations_processed": organizations_processed,
    }
