from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset
from apps.clients.models import Client, ClientContact
from apps.notifications.models import Notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.reports.models import DailyWorkOrderSummary
from apps.workorders.models import WorkOrder, WorkOrderUpdate


DEMO_PASSWORD = "Test@12345"


class Command(BaseCommand):
    help = "Seed local demo data for Maintolio demos and screenshots."

    def handle(self, *args, **options):
        with transaction.atomic():
            organization = self.seed_organization()
            users = self.seed_users(organization)
            clients = self.seed_clients(organization)
            contacts = self.seed_contacts(clients)
            assets = self.seed_assets(clients)
            work_orders = self.seed_work_orders(
                organization,
                clients,
                contacts,
                assets,
                users,
            )
            self.seed_updates(work_orders, users, contacts)
            notifications = self.seed_notifications(
                organization,
                work_orders,
                users,
                contacts,
            )
            self.seed_daily_summaries(organization)

        self.print_summary(
            organization=organization,
            users=users,
            clients=clients,
            assets=assets,
            work_orders=work_orders,
            notification_count=notifications,
        )

    def seed_organization(self):
        organization, _ = Organization.objects.update_or_create(
            name="TechCare Services Ltd.",
            defaults={
                "email": "info@techcare.test",
                "phone": "+8801700000000",
                "address": "Dhaka, Bangladesh",
                "is_active": True,
            },
        )
        return organization

    def seed_users(self, organization):
        demo_users = [
            ("owner@techcare.test", "Owner User", OrganizationMembership.Role.OWNER),
            ("admin@techcare.test", "Admin User", OrganizationMembership.Role.ADMIN),
            ("manager@techcare.test", "Manager User", OrganizationMembership.Role.MANAGER),
            (
                "technician1@techcare.test",
                "Technician One",
                OrganizationMembership.Role.TECHNICIAN,
            ),
            (
                "technician2@techcare.test",
                "Technician Two",
                OrganizationMembership.Role.TECHNICIAN,
            ),
        ]
        users = {}

        for email, full_name, role in demo_users:
            user = self.upsert_user(email=email, full_name=full_name)
            membership, _ = OrganizationMembership.objects.get_or_create(
                organization=organization,
                user=user,
                defaults={
                    "role": role,
                    "is_active": True,
                },
            )

            if membership.role != role or not membership.is_active:
                membership.role = role
                membership.is_active = True
                membership.save(update_fields=["role", "is_active", "updated_at"])

            users[email] = {
                "user": user,
                "membership": membership,
                "role": role,
            }

        return users

    def upsert_user(self, email, full_name, phone=""):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "phone": phone,
                "is_active": True,
            },
        )

        changed_fields = []

        if user.full_name != full_name:
            user.full_name = full_name
            changed_fields.append("full_name")

        if user.phone != phone:
            user.phone = phone
            changed_fields.append("phone")

        if not user.is_active:
            user.is_active = True
            changed_fields.append("is_active")

        user.set_password(DEMO_PASSWORD)
        changed_fields.append("password")
        user.save(update_fields=list(dict.fromkeys(changed_fields)))

        return user

    def seed_clients(self, organization):
        client_rows = [
            {
                "name": "ABC Hospital",
                "email": "facilities@abchospital.test",
                "phone": "+8801711111111",
                "industry": "Healthcare",
                "address": "Dhanmondi, Dhaka",
            },
            {
                "name": "Green Tower Apartments",
                "email": "admin@greentower.test",
                "phone": "+8801722222222",
                "industry": "Real Estate",
                "address": "Gulshan, Dhaka",
            },
            {
                "name": "North Star Factory",
                "email": "maintenance@northstar.test",
                "phone": "+8801733333333",
                "industry": "Manufacturing",
                "address": "Savar, Dhaka",
            },
        ]
        clients = {}

        for row in client_rows:
            client, _ = Client.objects.update_or_create(
                organization=organization,
                name=row["name"],
                defaults={
                    "email": row["email"],
                    "phone": row["phone"],
                    "industry": row["industry"],
                    "address": row["address"],
                    "is_active": True,
                },
            )
            clients[row["name"]] = client

        return clients

    def seed_contacts(self, clients):
        contacts = {}

        rahim_user = self.upsert_user(
            email="rahim@abchospital.test",
            full_name="Rahim Uddin",
            phone="+8801744444444",
        )

        contact_rows = [
            {
                "client": clients["ABC Hospital"],
                "email": "rahim@abchospital.test",
                "full_name": "Rahim Uddin",
                "phone": "+8801744444444",
                "position": "Facilities Manager",
                "can_login": True,
                "user": rahim_user,
                "is_primary": True,
            },
            {
                "client": clients["Green Tower Apartments"],
                "email": "nasrin@greentower.test",
                "full_name": "Nasrin Akter",
                "phone": "+8801755555555",
                "position": "Building Manager",
                "can_login": False,
                "user": None,
                "is_primary": True,
            },
            {
                "client": clients["North Star Factory"],
                "email": "kamal@northstar.test",
                "full_name": "Kamal Hossain",
                "phone": "+8801766666666",
                "position": "Plant Supervisor",
                "can_login": False,
                "user": None,
                "is_primary": True,
            },
        ]

        for row in contact_rows:
            contact, _ = ClientContact.objects.update_or_create(
                client=row["client"],
                email=row["email"],
                defaults={
                    "user": row["user"],
                    "full_name": row["full_name"],
                    "phone": row["phone"],
                    "position": row["position"],
                    "can_login": row["can_login"],
                    "is_primary": row["is_primary"],
                    "is_active": True,
                },
            )
            contacts[row["client"].name] = contact

        return contacts

    def seed_assets(self, clients):
        asset_rows = [
            ("ABC Hospital", "Backup Generator", "Generator", "ABC-GEN-001", "Basement"),
            ("ABC Hospital", "ICU Air Conditioner", "HVAC", "ABC-HVAC-ICU-01", "ICU"),
            ("ABC Hospital", "Water Pump", "Pump", "ABC-PUMP-001", "Utility Room"),
            ("Green Tower Apartments", "Elevator A", "Elevator", "GTA-ELEV-A", "Tower A"),
            (
                "Green Tower Apartments",
                "Fire Alarm Panel",
                "Fire Safety",
                "GTA-FIRE-001",
                "Security Room",
            ),
            (
                "Green Tower Apartments",
                "Basement Generator",
                "Generator",
                "GTA-GEN-BASE-01",
                "Basement",
            ),
            (
                "North Star Factory",
                "Compressor Unit",
                "Compressor",
                "NSF-COMP-001",
                "Production Floor",
            ),
            (
                "North Star Factory",
                "Production Line Motor",
                "Motor",
                "NSF-MOTOR-L1",
                "Line 1",
            ),
            (
                "North Star Factory",
                "Cooling Tower",
                "Cooling",
                "NSF-COOL-001",
                "Rooftop",
            ),
        ]
        assets = {}

        for client_name, name, asset_type, serial_number, location in asset_rows:
            asset, _ = Asset.objects.update_or_create(
                client=clients[client_name],
                serial_number=serial_number,
                defaults={
                    "name": name,
                    "asset_type": asset_type,
                    "location": location,
                    "status": Asset.Status.ACTIVE,
                },
            )
            assets[name] = asset

        return assets

    def seed_work_orders(self, organization, clients, contacts, assets, users):
        technician_one = users["technician1@techcare.test"]["membership"]
        technician_two = users["technician2@techcare.test"]["membership"]
        manager = users["manager@techcare.test"]["user"]
        owner = users["owner@techcare.test"]["user"]
        now = timezone.now()

        work_order_rows = [
            {
                "title": "Generator preventive maintenance",
                "client": clients["ABC Hospital"],
                "asset": assets["Backup Generator"],
                "requested_by_contact": contacts["ABC Hospital"],
                "priority": WorkOrder.Priority.HIGH,
                "status": WorkOrder.Status.ASSIGNED,
                "assigned_to": technician_one,
                "due_date": now + timedelta(days=2),
            },
            {
                "title": "ICU AC cooling issue",
                "client": clients["ABC Hospital"],
                "asset": assets["ICU Air Conditioner"],
                "requested_by_contact": contacts["ABC Hospital"],
                "priority": WorkOrder.Priority.URGENT,
                "status": WorkOrder.Status.IN_PROGRESS,
                "assigned_to": technician_two,
                "due_date": now + timedelta(hours=8),
            },
            {
                "title": "Water pump noise inspection",
                "client": clients["ABC Hospital"],
                "asset": assets["Water Pump"],
                "requested_by_contact": contacts["ABC Hospital"],
                "priority": WorkOrder.Priority.MEDIUM,
                "status": WorkOrder.Status.OPEN,
                "assigned_to": None,
                "due_date": now + timedelta(days=4),
            },
            {
                "title": "Elevator A vibration complaint",
                "client": clients["Green Tower Apartments"],
                "asset": assets["Elevator A"],
                "requested_by_contact": contacts["Green Tower Apartments"],
                "priority": WorkOrder.Priority.HIGH,
                "status": WorkOrder.Status.ON_HOLD,
                "assigned_to": technician_one,
                "due_date": now + timedelta(days=1),
            },
            {
                "title": "Fire alarm panel battery replacement",
                "client": clients["Green Tower Apartments"],
                "asset": assets["Fire Alarm Panel"],
                "requested_by_contact": contacts["Green Tower Apartments"],
                "priority": WorkOrder.Priority.MEDIUM,
                "status": WorkOrder.Status.COMPLETED,
                "assigned_to": technician_two,
                "due_date": now - timedelta(days=1),
            },
            {
                "title": "Basement generator oil leak",
                "client": clients["Green Tower Apartments"],
                "asset": assets["Basement Generator"],
                "requested_by_contact": contacts["Green Tower Apartments"],
                "priority": WorkOrder.Priority.URGENT,
                "status": WorkOrder.Status.OVERDUE,
                "assigned_to": technician_one,
                "due_date": now - timedelta(days=3),
            },
            {
                "title": "Compressor unit pressure drop",
                "client": clients["North Star Factory"],
                "asset": assets["Compressor Unit"],
                "requested_by_contact": contacts["North Star Factory"],
                "priority": WorkOrder.Priority.HIGH,
                "status": WorkOrder.Status.ASSIGNED,
                "assigned_to": technician_two,
                "due_date": now + timedelta(days=3),
            },
            {
                "title": "Production line motor overheating",
                "client": clients["North Star Factory"],
                "asset": assets["Production Line Motor"],
                "requested_by_contact": contacts["North Star Factory"],
                "priority": WorkOrder.Priority.URGENT,
                "status": WorkOrder.Status.IN_PROGRESS,
                "assigned_to": technician_one,
                "due_date": now + timedelta(hours=12),
            },
            {
                "title": "Cooling tower routine inspection",
                "client": clients["North Star Factory"],
                "asset": assets["Cooling Tower"],
                "requested_by_contact": contacts["North Star Factory"],
                "priority": WorkOrder.Priority.LOW,
                "status": WorkOrder.Status.CANCELLED,
                "assigned_to": None,
                "due_date": now + timedelta(days=7),
            },
            {
                "title": "Hospital generator load test",
                "client": clients["ABC Hospital"],
                "asset": assets["Backup Generator"],
                "requested_by_contact": contacts["ABC Hospital"],
                "priority": WorkOrder.Priority.MEDIUM,
                "status": WorkOrder.Status.OPEN,
                "assigned_to": None,
                "due_date": now + timedelta(days=6),
            },
        ]
        work_orders = {}

        for row in work_order_rows:
            work_order = WorkOrder.objects.filter(
                organization=organization,
                title=row["title"],
            ).first()

            defaults = {
                "client": row["client"],
                "asset": row["asset"],
                "description": f"Demo work order for {row['asset'].name}.",
                "priority": row["priority"],
                "status": row["status"],
                "created_by": manager if row["status"] != WorkOrder.Status.CANCELLED else owner,
                "requested_by_contact": row["requested_by_contact"],
                "assigned_to": row["assigned_to"],
                "due_date": row["due_date"],
            }

            if work_order:
                for field, value in defaults.items():
                    setattr(work_order, field, value)
                work_order.save()
            else:
                work_order = WorkOrder.objects.create(
                    organization=organization,
                    title=row["title"],
                    **defaults,
                )

            work_orders[row["title"]] = work_order

        return work_orders

    def seed_updates(self, work_orders, users, contacts):
        manager = users["manager@techcare.test"]["user"]
        technician_one = users["technician1@techcare.test"]["user"]
        technician_two = users["technician2@techcare.test"]["user"]
        rahim_user = contacts["ABC Hospital"].user

        update_rows = [
            (
                "Generator preventive maintenance",
                manager,
                "Assigned to Technician One.",
                WorkOrder.Status.OPEN,
                WorkOrder.Status.ASSIGNED,
                True,
            ),
            (
                "Generator preventive maintenance",
                technician_one,
                "Technician arrived on site and started inspection.",
                WorkOrder.Status.ASSIGNED,
                WorkOrder.Status.ASSIGNED,
                False,
            ),
            (
                "ICU AC cooling issue",
                rahim_user,
                "ICU temperature is rising quickly. Please prioritize.",
                WorkOrder.Status.IN_PROGRESS,
                WorkOrder.Status.IN_PROGRESS,
                False,
            ),
            (
                "ICU AC cooling issue",
                technician_two,
                "Filter cleaned; checking refrigerant pressure.",
                WorkOrder.Status.IN_PROGRESS,
                WorkOrder.Status.IN_PROGRESS,
                False,
            ),
            (
                "Elevator A vibration complaint",
                manager,
                "Waiting for vendor confirmation before continuing.",
                WorkOrder.Status.IN_PROGRESS,
                WorkOrder.Status.ON_HOLD,
                True,
            ),
            (
                "Fire alarm panel battery replacement",
                technician_two,
                "Battery replaced and panel tested successfully.",
                WorkOrder.Status.IN_PROGRESS,
                WorkOrder.Status.COMPLETED,
                False,
            ),
            (
                "Basement generator oil leak",
                manager,
                "Internal note: quote additional gasket replacement.",
                WorkOrder.Status.OVERDUE,
                WorkOrder.Status.OVERDUE,
                True,
            ),
        ]

        for title, user, message, old_status, new_status, is_internal in update_rows:
            work_order = work_orders[title]
            WorkOrderUpdate.objects.get_or_create(
                work_order=work_order,
                message=message,
                defaults={
                    "user": user,
                    "old_status": old_status,
                    "new_status": new_status,
                    "is_internal": is_internal,
                },
            )

    def seed_notifications(self, organization, work_orders, users, contacts):
        notification_rows = [
            (
                users["owner@techcare.test"]["user"],
                work_orders["ICU AC cooling issue"],
                "Urgent work order updated",
                "ICU AC cooling issue has a new technician update.",
                False,
            ),
            (
                users["manager@techcare.test"]["user"],
                work_orders["Water pump noise inspection"],
                "New client service request",
                "ABC Hospital created Water pump noise inspection.",
                False,
            ),
            (
                users["technician1@techcare.test"]["user"],
                work_orders["Generator preventive maintenance"],
                "New work order assigned",
                "Work order Generator preventive maintenance has been assigned to you.",
                False,
            ),
            (
                users["technician2@techcare.test"]["user"],
                work_orders["Fire alarm panel battery replacement"],
                "Work order completed",
                "Fire alarm panel battery replacement was completed.",
                True,
            ),
        ]

        client_user = contacts["ABC Hospital"].user
        if client_user:
            notification_rows.append(
                (
                    client_user,
                    work_orders["ICU AC cooling issue"],
                    "New work order update",
                    "New update added to ICU AC cooling issue.",
                    False,
                )
            )

        for user, work_order, title, message, is_read in notification_rows:
            Notification.objects.update_or_create(
                user=user,
                work_order=work_order,
                title=title,
                defaults={
                    "message": message,
                    "organization": organization,
                    "is_read": is_read,
                },
            )

        demo_user_ids = [
            row["user"].id for row in users.values()
        ]
        if client_user:
            demo_user_ids.append(client_user.id)

        return Notification.objects.filter(user_id__in=demo_user_ids).count()

    def seed_daily_summaries(self, organization):
        today = timezone.localdate()

        for offset in range(7):
            summary_date = today - timedelta(days=offset)
            work_orders = WorkOrder.objects.filter(
                organization=organization,
                created_at__date=summary_date,
            )

            DailyWorkOrderSummary.objects.update_or_create(
                organization=organization,
                date=summary_date,
                defaults={
                    "total_work_orders": work_orders.count(),
                    "open_work_orders": work_orders.filter(status=WorkOrder.Status.OPEN).count(),
                    "assigned_work_orders": work_orders.filter(
                        status=WorkOrder.Status.ASSIGNED
                    ).count(),
                    "in_progress_work_orders": work_orders.filter(
                        status=WorkOrder.Status.IN_PROGRESS
                    ).count(),
                    "on_hold_work_orders": work_orders.filter(
                        status=WorkOrder.Status.ON_HOLD
                    ).count(),
                    "completed_work_orders": work_orders.filter(
                        status=WorkOrder.Status.COMPLETED
                    ).count(),
                    "cancelled_work_orders": work_orders.filter(
                        status=WorkOrder.Status.CANCELLED
                    ).count(),
                    "overdue_work_orders": work_orders.filter(
                        status=WorkOrder.Status.OVERDUE
                    ).count(),
                    "urgent_work_orders": work_orders.filter(
                        priority=WorkOrder.Priority.URGENT
                    ).count(),
                },
            )

    def print_summary(
        self,
        organization,
        users,
        clients,
        assets,
        work_orders,
        notification_count,
    ):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write(f"Organization: {organization.name}")
        self.stdout.write("")
        self.stdout.write("Demo users:")

        for email, row in users.items():
            self.stdout.write(
                f"- {row['user'].full_name} ({row['role']}): {email} / {DEMO_PASSWORD}"
            )

        self.stdout.write(f"- Rahim Uddin (CLIENT): rahim@abchospital.test / {DEMO_PASSWORD}")
        self.stdout.write("")
        self.stdout.write(f"Clients: {len(clients)}")
        self.stdout.write(f"Assets: {len(assets)}")
        self.stdout.write(f"Work orders: {len(work_orders)}")
        self.stdout.write(f"Notifications: {notification_count}")
