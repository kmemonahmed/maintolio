from rest_framework import serializers

from .models import Organization, OrganizationMembership


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
            "email",
            "phone",
            "website",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "is_active",
            "created_at",
            "updated_at",
        )


class CurrentOrganizationResponseSerializer(serializers.Serializer):
    organization = OrganizationSerializer()
    membership = serializers.SerializerMethodField()

    def get_membership(self, obj):
        membership = obj["membership"]

        return {
            "id": membership.id,
            "role": membership.role,
            "is_active": membership.is_active,
        }