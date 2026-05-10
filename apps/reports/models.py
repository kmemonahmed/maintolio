from django.db import models

from apps.core.models import BaseModel


class DailyWorkOrderSummary(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="daily_work_order_summaries"
    )

    date = models.DateField()

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
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "date"],
                name="unique_daily_summary_per_organization"
            )
        ]
        indexes = [
            models.Index(fields=["organization", "date"]),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.date}"