from django.contrib import admin

from .models import Client, ClientContact


class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 0
    autocomplete_fields = ("user",)
    fields = (
        "full_name",
        "email",
        "phone",
        "position",
        "user",
        "is_primary",
        "can_login",
        "is_active",
    )
    show_change_link = True


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "email",
        "phone",
        "industry",
        "is_active",
        "contacts_count",
        "assets_count",
        "work_orders_count",
        "created_at",
    )
    list_filter = (
        "organization",
        "industry",
        "is_active",
        "created_at",
    )
    search_fields = (
        "name",
        "email",
        "phone",
        "industry",
        "organization__name",
    )
    autocomplete_fields = ("organization",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("name",)
    list_select_related = ("organization",)
    inlines = [ClientContactInline]

    @admin.display(description="Contacts")
    def contacts_count(self, obj):
        return obj.contacts.count()

    @admin.display(description="Assets")
    def assets_count(self, obj):
        return obj.assets.count()

    @admin.display(description="Work orders")
    def work_orders_count(self, obj):
        return obj.work_orders.count()


@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "client",
        "organization_name",
        "email",
        "phone",
        "position",
        "user",
        "is_primary",
        "can_login",
        "is_active",
    )
    list_filter = (
        "client__organization",
        "is_primary",
        "can_login",
        "is_active",
    )
    search_fields = (
        "full_name",
        "email",
        "phone",
        "position",
        "client__name",
        "client__organization__name",
        "user__email",
        "user__full_name",
    )
    autocomplete_fields = (
        "client",
        "user",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = (
        "client__name",
        "full_name",
    )
    list_select_related = (
        "client",
        "client__organization",
        "user",
    )

    @admin.display(description="Organization")
    def organization_name(self, obj):
        return obj.client.organization.name