from django.urls import path

from .views import (
    DailyWorkOrderSummaryView,
    DashboardSummaryView,
    WorkOrderSummaryView,
)


urlpatterns = [
    path(
        "dashboard-summary/",
        DashboardSummaryView.as_view(),
        name="dashboard_summary",
    ),
    path(
        "work-order-summary/",
        WorkOrderSummaryView.as_view(),
        name="work_order_summary",
    ),
    path(
        "daily-work-order-summary/",
        DailyWorkOrderSummaryView.as_view(),
        name="daily_work_order_summary",
    ),
]