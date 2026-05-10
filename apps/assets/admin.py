from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "client",
        "asset_type",
        "serial_number",
        "status",
        "last_service_date",
        "created_at",
    )
    list_filter = ("status", "asset_type")
    search_fields = (
        "name",
        "asset_type",
        "serial_number",
        "location",
        "client__name",
    )
    autocomplete_fields = ("client",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")