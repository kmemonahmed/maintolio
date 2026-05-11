from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class WorkOrder(BaseModel):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        ON_HOLD = "ON_HOLD", "On Hold"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        OVERDUE = "OVERDUE", "Overdue"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="work_orders"
    )

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="work_orders"
    )

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="work_orders"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_work_orders"
    )

    requested_by_contact = models.ForeignKey(
        "clients.ClientContact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_work_orders"
    )

    assigned_to = models.ForeignKey(
        "organizations.OrganizationMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_work_orders"
    )

    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "priority"]),
            models.Index(fields=["client", "status"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"#{self.id} - {self.title}"

    def clean(self):
        if self.client and self.organization:
            if self.client.organization_id != self.organization_id:
                raise ValidationError(
                    "Selected client does not belong to this organization."
                )

        if self.asset and self.client:
            if self.asset.client_id != self.client_id:
                raise ValidationError(
                    "Selected asset does not belong to this client."
                )

        if self.requested_by_contact and self.client:
            if self.requested_by_contact.client_id != self.client_id:
                raise ValidationError(
                    "Requested-by contact does not belong to this client."
                )

        if self.assigned_to:
            if self.assigned_to.organization_id != self.organization_id:
                raise ValidationError(
                    "Assigned technician must belong to the same organization."
                )

            if self.assigned_to.role != "TECHNICIAN":
                raise ValidationError(
                    "Work order can only be assigned to a technician membership."
                )

            if not self.assigned_to.is_active:
                raise ValidationError(
                    "Cannot assign work order to an inactive technician."
                )

    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()

        if self.status == self.Status.CANCELLED and not self.cancelled_at:
            self.cancelled_at = timezone.now()

        if self.status != self.Status.COMPLETED:
            self.completed_at = None

        if self.status != self.Status.CANCELLED:
            self.cancelled_at = None

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if not self.due_date:
            return False

        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return False

        return timezone.now() > self.due_date


class WorkOrderUpdate(BaseModel):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="updates"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="work_order_updates"
    )

    message = models.TextField(blank=True)

    old_status = models.CharField(
        max_length=30,
        choices=WorkOrder.Status.choices,
        blank=True
    )

    new_status = models.CharField(
        max_length=30,
        choices=WorkOrder.Status.choices,
        blank=True
    )

    is_internal = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["work_order", "created_at"]),
            models.Index(fields=["is_internal"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"Update for WorkOrder #{self.work_order_id}"


class Attachment(BaseModel):
    class FileType(models.TextChoices):
        IMAGE = "IMAGE", "Image"
        DOCUMENT = "DOCUMENT", "Document"
        OTHER = "OTHER", "Other"

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_attachments"
    )

    file = models.FileField(upload_to="work_order_attachments/")

    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER
    )

    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["work_order", "file_type"]),
        ]

    def __str__(self):
        return f"Attachment for WorkOrder #{self.work_order_id}"