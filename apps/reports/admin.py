from django.contrib import admin

from .models import DailyWorkOrderSummary


@admin.register(DailyWorkOrderSummary)
class DailyWorkOrderSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "total_work_orders",
        "open_work_orders",
        "assigned_work_orders",
        "in_progress_work_orders",
        "completed_work_orders",
        "cancelled_work_orders",
        "overdue_work_orders",
        "urgent_work_orders",
        "created_at",
    )
    list_filter = ("date",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-date",)
    date_hierarchy = "date"