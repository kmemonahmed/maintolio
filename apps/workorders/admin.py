from django.contrib import admin

from .models import WorkOrder, WorkOrderUpdate, Attachment


class WorkOrderUpdateInline(admin.TabularInline):
    model = WorkOrderUpdate
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("user", "message", "old_status", "new_status", "created_at")


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("uploaded_by", "file", "file_type", "description", "created_at")


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "company",
        "client",
        "asset",
        "priority",
        "status",
        "assigned_to",
        "due_date",
        "completed_at",
        "created_at",
    )
    list_filter = (
        "status",
        "priority",
        "company",
        "client",
        "assigned_to",
    )
    search_fields = (
        "title",
        "description",
        "company__name",
        "client__name",
        "asset__name",
        "asset__serial_number",
        "created_by__email",
        "assigned_to__email",
    )
    autocomplete_fields = (
        "company",
        "client",
        "asset",
        "created_by",
        "assigned_to",
    )
    readonly_fields = ("created_at", "updated_at", "completed_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = [WorkOrderUpdateInline, AttachmentInline]


@admin.register(WorkOrderUpdate)
class WorkOrderUpdateAdmin(admin.ModelAdmin):
    list_display = (
        "work_order",
        "user",
        "old_status",
        "new_status",
        "created_at",
    )
    list_filter = ("old_status", "new_status")
    search_fields = (
        "work_order__title",
        "user__email",
        "user__full_name",
        "message",
    )
    autocomplete_fields = ("work_order", "user")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "work_order",
        "uploaded_by",
        "file_type",
        "description",
        "created_at",
    )
    list_filter = ("file_type",)
    search_fields = (
        "work_order__title",
        "uploaded_by__email",
        "uploaded_by__full_name",
        "description",
    )
    autocomplete_fields = ("work_order", "uploaded_by")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)