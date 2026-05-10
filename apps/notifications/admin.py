from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read",)
    search_fields = (
        "title",
        "message",
        "user__email",
        "user__full_name",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)