from rest_framework import serializers

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership
from django.db import transaction
from django.contrib.auth.password_validation import validate_password




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


TEAM_MEMBER_ROLE_CHOICES = (
    (OrganizationMembership.Role.ADMIN, "Admin"),
    (OrganizationMembership.Role.MANAGER, "Manager"),
    (OrganizationMembership.Role.TECHNICIAN, "Technician"),
)


class TeamMemberUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone",
            "is_active",
        )


class TeamMemberSerializer(serializers.ModelSerializer):
    user = TeamMemberUserSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = (
            "id",
            "user",
            "role",
            "is_active",
            "joined_at",
            "created_at",
            "updated_at",
        )


class TeamMemberCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=TEAM_MEMBER_ROLE_CHOICES)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate_email(self, value):
        return value.lower().strip()

    def validate(self, attrs):
        email = attrs["email"]
        organization = self.context["current_membership"].organization

        if OrganizationMembership.objects.filter(
            organization=organization,
            user__email=email,
        ).exists():
            raise serializers.ValidationError(
                {"email": "This user is already a member of this organization."}
            )

        user_exists = User.objects.filter(email=email).exists()

        if not user_exists and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "Password is required when creating a new user."}
            )

        if not user_exists:
            validate_password(attrs["password"])

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        current_membership = self.context["current_membership"]
        organization = current_membership.organization

        email = validated_data["email"]
        user = User.objects.filter(email=email).first()

        if not user:
            user = User.objects.create_user(
                email=email,
                password=validated_data["password"],
                full_name=validated_data["full_name"],
                phone=validated_data.get("phone", ""),
            )

        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            role=validated_data["role"],
            is_active=True,
            invited_by=current_membership.user,
        )

        return membership


class TeamMemberUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=TEAM_MEMBER_ROLE_CHOICES,
        required=False,
    )
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        membership = self.instance
        current_membership = self.context["current_membership"]

        if membership.role == OrganizationMembership.Role.OWNER:
            if "role" in attrs:
                raise serializers.ValidationError(
                    {"role": "Owner role cannot be changed from this endpoint."}
                )

            if attrs.get("is_active") is False:
                raise serializers.ValidationError(
                    {"is_active": "Owner membership cannot be deactivated from this endpoint."}
                )

        if membership.id == current_membership.id and attrs.get("is_active") is False:
            raise serializers.ValidationError(
                {"is_active": "You cannot deactivate your own membership."}
            )

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user

        if "full_name" in validated_data:
            user.full_name = validated_data["full_name"]

        if "phone" in validated_data:
            user.phone = validated_data["phone"]

        user.save(update_fields=["full_name", "phone"])

        if "role" in validated_data:
            instance.role = validated_data["role"]

        if "is_active" in validated_data:
            instance.is_active = validated_data["is_active"]

        instance.save(update_fields=["role", "is_active", "updated_at"])

        return instance