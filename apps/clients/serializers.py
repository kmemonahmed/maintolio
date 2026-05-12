from rest_framework import serializers

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    organization = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Client
        fields = (
            "id",
            "organization",
            "name",
            "email",
            "phone",
            "address",
            "industry",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "organization",
            "created_at",
            "updated_at",
        )


class ClientCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "name",
            "email",
            "phone",
            "address",
            "industry",
            "notes",
            "is_active",
        )