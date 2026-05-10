from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Notification(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    work_order = models.ForeignKey(
        "workorders.WorkOrder",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    title = models.CharField(max_length=150)
    message = models.TextField()

    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["organization", "created_at"]),
        ]

    def __str__(self):
        return self.title