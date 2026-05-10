from django.db import models

from apps.core.models import BaseModel


class Asset(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Under Maintenance"
        RETIRED = "RETIRED", "Retired"

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="assets"
    )

    name = models.CharField(max_length=150)
    asset_type = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    installed_at = models.DateField(null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.serial_number}"