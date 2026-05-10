from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "client",
        "organization_name",
        "asset_type",
        "serial_number",
        "status",
        "location",
        "last_service_date",
        "created_at",
    )
    list_filter = (
        "status",
        "asset_type",
        "client__organization",
        "created_at",
    )
    search_fields = (
        "name",
        "asset_type",
        "serial_number",
        "location",
        "client__name",
        "client__organization__name",
    )
    autocomplete_fields = ("client",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("name",)
    list_select_related = (
        "client",
        "client__organization",
    )

    @admin.display(description="Organization")
    def organization_name(self, obj):
        return obj.client.organization.name