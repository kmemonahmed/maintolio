from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_clients = serializers.IntegerField()
    total_assets = serializers.IntegerField()
    total_team_members = serializers.IntegerField()

    total_work_orders = serializers.IntegerField()
    open_work_orders = serializers.IntegerField()
    assigned_work_orders = serializers.IntegerField()
    in_progress_work_orders = serializers.IntegerField()
    on_hold_work_orders = serializers.IntegerField()
    completed_work_orders = serializers.IntegerField()
    cancelled_work_orders = serializers.IntegerField()
    overdue_work_orders = serializers.IntegerField()

    low_priority_work_orders = serializers.IntegerField()
    medium_priority_work_orders = serializers.IntegerField()
    high_priority_work_orders = serializers.IntegerField()
    urgent_priority_work_orders = serializers.IntegerField()

    unread_notifications = serializers.IntegerField()


class WorkOrderSummarySerializer(serializers.Serializer):
    date_from = serializers.DateField(allow_null=True)
    date_to = serializers.DateField(allow_null=True)

    total_work_orders = serializers.IntegerField()
    assigned_work_orders = serializers.IntegerField()
    unassigned_work_orders = serializers.IntegerField()

    overdue_work_orders = serializers.IntegerField()
    due_today_work_orders = serializers.IntegerField()

    status_breakdown = serializers.DictField(
        child=serializers.IntegerField()
    )
    priority_breakdown = serializers.DictField(
        child=serializers.IntegerField()
    )


class DailyWorkOrderSummaryItemSerializer(serializers.Serializer):
    date = serializers.DateField()

    total_work_orders = serializers.IntegerField()
    open_work_orders = serializers.IntegerField()
    assigned_work_orders = serializers.IntegerField()
    in_progress_work_orders = serializers.IntegerField()
    on_hold_work_orders = serializers.IntegerField()
    completed_work_orders = serializers.IntegerField()
    cancelled_work_orders = serializers.IntegerField()

    low_priority_work_orders = serializers.IntegerField()
    medium_priority_work_orders = serializers.IntegerField()
    high_priority_work_orders = serializers.IntegerField()
    urgent_priority_work_orders = serializers.IntegerField()


class DailyWorkOrderSummarySerializer(serializers.Serializer):
    date_from = serializers.DateField(allow_null=True)
    date_to = serializers.DateField(allow_null=True)
    results = DailyWorkOrderSummaryItemSerializer(many=True)