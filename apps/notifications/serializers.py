from rest_framework import serializers

from .models import Notification


class NotificationWorkOrderMiniSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()


class NotificationSerializer(serializers.ModelSerializer):
    organization = serializers.StringRelatedField(read_only=True)
    work_order = NotificationWorkOrderMiniSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "organization",
            "work_order",
            "title",
            "message",
            "is_read",
            "created_at",
            "updated_at",
        )