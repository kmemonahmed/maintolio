from rest_framework import serializers

from apps.clients.models import Client
from apps.clients.serializers import ClientMiniSerializer

from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    client = ClientMiniSerializer(read_only=True)

    class Meta:
        model = Asset
        fields = (
            "id",
            "client",
            "name",
            "asset_type",
            "serial_number",
            "location",
            "status",
            "installed_at",
            "last_service_date",
            "created_at",
            "updated_at",
        )


class AssetCreateUpdateSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.none()
    )

    class Meta:
        model = Asset
        fields = (
            "client",
            "name",
            "asset_type",
            "serial_number",
            "location",
            "status",
            "installed_at",
            "last_service_date",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_membership = self.context.get("current_membership")

        if current_membership:
            self.fields["client"].queryset = Client.objects.filter(
                organization=current_membership.organization,
                is_active=True,
            )
        else:
            self.fields["client"].queryset = Client.objects.none()

    def validate(self, attrs):
        current_membership = self.context.get("current_membership")
        client = attrs.get("client") or getattr(self.instance, "client", None)

        if current_membership and client:
            if client.organization_id != current_membership.organization_id:
                raise serializers.ValidationError(
                    {"client": "Selected client does not belong to your organization."}
                )

        return attrs