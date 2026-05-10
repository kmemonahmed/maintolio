from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "organization",
        "work_order",
        "is_read",
        "created_at",
    )
    list_filter = (
        "is_read",
        "organization",
        "created_at",
    )
    search_fields = (
        "title",
        "message",
        "user__email",
        "user__full_name",
        "organization__name",
        "work_order__title",
    )
    autocomplete_fields = (
        "user",
        "organization",
        "work_order",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    list_select_related = (
        "user",
        "organization",
        "work_order",
    )

    actions = (
        "mark_as_read",
        "mark_as_unread",
    )

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected notifications as unread")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)