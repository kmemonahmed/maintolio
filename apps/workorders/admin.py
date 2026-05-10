from django.contrib import admin

from .models import Attachment, WorkOrder, WorkOrderUpdate


class WorkOrderUpdateInline(admin.TabularInline):
    model = WorkOrderUpdate
    extra = 0
    autocomplete_fields = ("user",)
    fields = (
        "user",
        "message",
        "old_status",
        "new_status",
        "is_internal",
        "created_at",
    )
    readonly_fields = ("created_at",)
    show_change_link = True


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    autocomplete_fields = ("uploaded_by",)
    fields = (
        "uploaded_by",
        "file",
        "file_type",
        "description",
        "created_at",
    )
    readonly_fields = ("created_at",)
    show_change_link = True


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "organization",
        "client",
        "asset",
        "priority",
        "status",
        "assigned_to",
        "due_date",
        "is_overdue_display",
        "completed_at",
        "created_at",
    )
    list_filter = (
        "organization",
        "status",
        "priority",
        "client",
        "assigned_to",
        "created_at",
        "due_date",
    )
    search_fields = (
        "id",
        "title",
        "description",
        "organization__name",
        "client__name",
        "asset__name",
        "asset__serial_number",
        "created_by__email",
        "created_by__full_name",
        "assigned_to__user__email",
        "assigned_to__user__full_name",
        "requested_by_contact__full_name",
        "requested_by_contact__email",
    )
    autocomplete_fields = (
        "organization",
        "client",
        "asset",
        "created_by",
        "requested_by_contact",
        "assigned_to",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
        "cancelled_at",
        "is_overdue_display",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "organization",
        "client",
        "asset",
        "created_by",
        "requested_by_contact",
        "assigned_to",
        "assigned_to__user",
    )
    inlines = [
        WorkOrderUpdateInline,
        AttachmentInline,
    ]

    fieldsets = (
        (
            "Main Information",
            {
                "fields": (
                    "organization",
                    "client",
                    "asset",
                    "title",
                    "description",
                )
            },
        ),
        (
            "Workflow",
            {
                "fields": (
                    "priority",
                    "status",
                    "assigned_to",
                    "due_date",
                    "completed_at",
                    "cancelled_at",
                    "is_overdue_display",
                )
            },
        ),
        (
            "Request Information",
            {
                "fields": (
                    "created_by",
                    "requested_by_contact",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Overdue", boolean=True)
    def is_overdue_display(self, obj):
        return obj.is_overdue


@admin.register(WorkOrderUpdate)
class WorkOrderUpdateAdmin(admin.ModelAdmin):
    list_display = (
        "work_order",
        "organization_name",
        "user",
        "old_status",
        "new_status",
        "is_internal",
        "created_at",
    )
    list_filter = (
        "is_internal",
        "old_status",
        "new_status",
        "work_order__organization",
        "created_at",
    )
    search_fields = (
        "work_order__title",
        "work_order__client__name",
        "work_order__organization__name",
        "user__email",
        "user__full_name",
        "message",
    )
    autocomplete_fields = (
        "work_order",
        "user",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    list_select_related = (
        "work_order",
        "work_order__organization",
        "user",
    )

    @admin.display(description="Organization")
    def organization_name(self, obj):
        return obj.work_order.organization.name


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "work_order",
        "organization_name",
        "uploaded_by",
        "file_type",
        "description",
        "created_at",
    )
    list_filter = (
        "file_type",
        "work_order__organization",
        "created_at",
    )
    search_fields = (
        "work_order__title",
        "work_order__client__name",
        "work_order__organization__name",
        "uploaded_by__email",
        "uploaded_by__full_name",
        "description",
    )
    autocomplete_fields = (
        "work_order",
        "uploaded_by",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    list_select_related = (
        "work_order",
        "work_order__organization",
        "uploaded_by",
    )

    @admin.display(description="Organization")
    def organization_name(self, obj):
        return obj.work_order.organization.name