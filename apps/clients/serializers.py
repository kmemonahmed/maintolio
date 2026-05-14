from rest_framework import serializers

from .models import Client, ClientContact


from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction


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


User = get_user_model()


class ClientMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "industry",
        )


class ClientContactUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "phone",
            "is_active",
        )


class ClientContactSerializer(serializers.ModelSerializer):
    client = ClientMiniSerializer(read_only=True)
    user = ClientContactUserSerializer(read_only=True)

    class Meta:
        model = ClientContact
        fields = (
            "id",
            "client",
            "user",
            "full_name",
            "email",
            "phone",
            "position",
            "is_primary",
            "can_login",
            "is_active",
            "created_at",
            "updated_at",
        )


class ClientContactCreateSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.none()
    )
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(default=False)
    can_login = serializers.BooleanField(default=False)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
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

    def validate_email(self, value):
        return value.lower().strip()

    def validate(self, attrs):
        can_login = attrs.get("can_login", False)
        email = attrs["email"]

        if can_login:
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                if hasattr(existing_user, "client_contact_profile"):
                    raise serializers.ValidationError(
                        {
                            "email": "This user is already linked to a client contact profile."
                        }
                    )
            else:
                password = attrs.get("password")

                if not password:
                    raise serializers.ValidationError(
                        {
                            "password": "Password is required when creating login access for a new client contact."
                        }
                    )

                validate_password(password)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password", "")
        can_login = validated_data.get("can_login", False)
        email = validated_data["email"]

        user = None

        if can_login:
            user = User.objects.filter(email=email).first()

            if not user:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    full_name=validated_data["full_name"],
                    phone=validated_data.get("phone", ""),
                )

        client_contact = ClientContact.objects.create(
            user=user,
            **validated_data,
        )

        if client_contact.is_primary:
            ClientContact.objects.filter(
                client=client_contact.client,
                is_primary=True,
            ).exclude(id=client_contact.id).update(is_primary=False)

        return client_contact


class ClientContactUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(required=False)
    can_login = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_email(self, value):
        return value.lower().strip()

    def validate(self, attrs):
        instance = self.instance

        if attrs.get("can_login") is True and not instance.user:
            raise serializers.ValidationError(
                {
                    "can_login": "This contact is not linked to a user account. Create login access separately later."
                }
            )

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        if "full_name" in validated_data:
            instance.full_name = validated_data["full_name"]

        if "email" in validated_data:
            instance.email = validated_data["email"]

        if "phone" in validated_data:
            instance.phone = validated_data["phone"]

        if "position" in validated_data:
            instance.position = validated_data["position"]

        if "is_primary" in validated_data:
            instance.is_primary = validated_data["is_primary"]

        if "can_login" in validated_data:
            instance.can_login = validated_data["can_login"]

        if "is_active" in validated_data:
            instance.is_active = validated_data["is_active"]

        instance.save()

        if instance.user:
            updated_user_fields = []

            if "full_name" in validated_data:
                instance.user.full_name = instance.full_name
                updated_user_fields.append("full_name")

            if "phone" in validated_data:
                instance.user.phone = instance.phone
                updated_user_fields.append("phone")

            if updated_user_fields:
                instance.user.save(update_fields=updated_user_fields)

        if instance.is_primary:
            ClientContact.objects.filter(
                client=instance.client,
                is_primary=True,
            ).exclude(id=instance.id).update(is_primary=False)

        return instance