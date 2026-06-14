from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.clients.models import ClientContact
from apps.organizations.models import OrganizationMembership
from .models import User


class OrganizationMembershipInline(admin.TabularInline):
    model = OrganizationMembership
    fk_name = "user"
    extra = 0
    autocomplete_fields = ("organization", "invited_by")
    fields = ("organization", "role", "is_active", "joined_at", "invited_by")
    readonly_fields = ("joined_at",)
    show_change_link = True


class ClientContactInline(admin.StackedInline):
    model = ClientContact
    fk_name = "user"
    extra = 0
    max_num = 1
    autocomplete_fields = ("client",)
    fields = (
        "client",
        "full_name",
        "email",
        "phone",
        "position",
        "is_primary",
        "can_login",
        "is_active",
    )
    show_change_link = True


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        "email",
        "full_name",
        "phone",
        "is_staff",
        "is_superuser",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    )
    search_fields = (
        "email",
        "full_name",
        "phone",
    )
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "phone", "avatar")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "phone",
                    "avatar",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    readonly_fields = (
        "last_login",
        "date_joined",
        "created_at",
        "updated_at",
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    inlines = [
        OrganizationMembershipInline,
        ClientContactInline,
    ]
