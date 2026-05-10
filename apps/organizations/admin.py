from django.contrib import admin

from .models import Organization, OrganizationMembership


class OrganizationMembershipInline(admin.TabularInline):
    model = OrganizationMembership
    extra = 0
    autocomplete_fields = ("user", "invited_by")
    fields = (
        "user",
        "role",
        "is_active",
        "joined_at",
        "invited_by",
    )
    readonly_fields = ("joined_at",)
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "email",
        "phone",
        "is_active",
        "members_count",
        "clients_count",
        "work_orders_count",
        "created_at",
    )
    list_filter = (
        "is_active",
        "created_at",
    )
    search_fields = (
        "name",
        "slug",
        "email",
        "phone",
        "website",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("name",)
    inlines = [OrganizationMembershipInline]

    @admin.display(description="Members")
    def members_count(self, obj):
        return obj.memberships.count()

    @admin.display(description="Clients")
    def clients_count(self, obj):
        return obj.clients.count()

    @admin.display(description="Work orders")
    def work_orders_count(self, obj):
        return obj.work_orders.count()


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "organization",
        "role",
        "is_active",
        "joined_at",
        "invited_by",
    )
    list_filter = (
        "role",
        "is_active",
        "organization",
    )
    search_fields = (
        "user__email",
        "user__full_name",
        "organization__name",
        "organization__slug",
    )
    autocomplete_fields = (
        "organization",
        "user",
        "invited_by",
    )
    readonly_fields = (
        "joined_at",
        "created_at",
        "updated_at",
    )
    ordering = (
        "organization__name",
        "role",
        "user__email",
    )
    list_select_related = (
        "organization",
        "user",
        "invited_by",
    )

    actions = (
        "activate_memberships",
        "deactivate_memberships",
    )

    @admin.action(description="Activate selected memberships")
    def activate_memberships(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected memberships")
    def deactivate_memberships(self, request, queryset):
        queryset.update(is_active=False)