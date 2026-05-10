from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
        "account",
        "email",
        "phone",
        "contact_person",
        "created_at",
    )
    list_filter = ("company",)
    search_fields = (
        "name",
        "email",
        "phone",
        "contact_person",
        "company__name",
        "account__email",
        "account__full_name",
    )
    autocomplete_fields = ("company", "account")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")