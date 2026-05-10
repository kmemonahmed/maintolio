from django.db import models

from apps.core.models import BaseModel


class DailyWorkOrderSummary(BaseModel):
    date = models.DateField(unique=True)

    total_work_orders = models.PositiveIntegerField(default=0)
    open_work_orders = models.PositiveIntegerField(default=0)
    assigned_work_orders = models.PositiveIntegerField(default=0)
    in_progress_work_orders = models.PositiveIntegerField(default=0)
    on_hold_work_orders = models.PositiveIntegerField(default=0)
    completed_work_orders = models.PositiveIntegerField(default=0)
    cancelled_work_orders = models.PositiveIntegerField(default=0)
    overdue_work_orders = models.PositiveIntegerField(default=0)
    urgent_work_orders = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Daily work order summaries"

    def __str__(self):
        return f"Work order summary - {self.date}"