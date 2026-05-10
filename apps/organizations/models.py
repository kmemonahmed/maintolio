from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)


class OrganizationMembership(BaseModel):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        TECHNICIAN = "TECHNICIAN", "Technician"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices
    )

    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_organization_invitations"
    )

    class Meta:
        ordering = ["organization__name", "role", "user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_user_per_organization"
            )
        ]
        indexes = [
            models.Index(fields=["organization", "role"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"