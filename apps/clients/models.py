from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel


class Client(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="clients"
    )

    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    industry = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_client_name_per_organization"
            )
        ]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class ClientContact(BaseModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="contacts"
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_contact_profile"
    )

    full_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    position = models.CharField(max_length=100, blank=True)

    is_primary = models.BooleanField(default=False)
    can_login = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["client__name", "full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "email"],
                name="unique_contact_email_per_client"
            )
        ]
        indexes = [
            models.Index(fields=["client", "is_active"]),
            models.Index(fields=["email"]),
            models.Index(fields=["can_login"]),
        ]

    def clean(self):
        if self.can_login and not self.user:
            raise ValidationError(
                "A client contact must be linked to a user account if can_login=True."
            )

        if self.user:
            if not self.full_name:
                self.full_name = self.user.full_name

            if not self.email:
                self.email = self.user.email

            if not self.phone:
                self.phone = self.user.phone

        if not self.full_name:
            raise ValidationError("Full name is required.")

        if not self.email:
            raise ValidationError("Email is required.")

    def save(self, *args, **kwargs):
        if self.user:
            if not self.full_name:
                self.full_name = self.user.full_name

            if not self.email:
                self.email = self.user.email

            if not self.phone:
                self.phone = self.user.phone

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.client.name}"