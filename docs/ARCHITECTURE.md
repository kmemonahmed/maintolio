# Architecture

Maintolio is a modular Django REST Framework backend for a multi-tenant B2B SaaS work order platform. The system is organized by business domain, with tenant isolation enforced through organization membership and scoped querysets.

## Multi-Tenant Design

The top-level tenant is `Organization`. Company-side users access data through an active `OrganizationMembership`. Most company APIs resolve the current membership from the authenticated user and use that membership's organization to scope clients, assets, work orders, team members, reports, and notifications.

This means records from one organization should not be visible or mutable from another organization.

## User vs OrganizationMembership

`User` is the authentication identity. It stores login credentials and profile information.

`OrganizationMembership` connects a user to an organization and assigns a role:

- `OWNER`
- `ADMIN`
- `MANAGER`
- `TECHNICIAN`

This separation allows a user identity to be independent from organization-specific access rules.

## Client vs ClientContact

`Client` represents a customer business, facility, or account served by the organization.

`ClientContact` represents a person at a client. Some client contacts can log in to the client portal when linked to a `User` and marked with login access.

Client contacts can create service requests and view public work order updates for their own client. They cannot access other clients' data.

## Assets

Assets belong to clients. Work orders can optionally reference an asset, allowing service providers to track maintenance history against client-owned equipment.

Typical asset data includes:

- name
- asset type
- serial number
- location
- status
- installed date
- last service date

## WorkOrder Lifecycle

Work orders belong to an organization and client, and may be linked to an asset and requesting client contact.

Supported statuses include:

- `OPEN`
- `ASSIGNED`
- `IN_PROGRESS`
- `ON_HOLD`
- `COMPLETED`
- `CANCELLED`
- `OVERDUE`

Typical lifecycle:

1. Work order is created by a company user or client contact.
2. Manager assigns a technician.
3. Technician or company user changes status.
4. Users add public or internal updates.
5. Attachments can be uploaded.
6. Work order is completed, cancelled, or marked overdue.

Internal updates are hidden from the client portal. Public updates can be visible to client contacts.

## Technician Portal

Technicians use dedicated APIs scoped to work orders assigned to their own active membership. This avoids exposing all company work orders to technician users.

## Client Portal

Client contacts use dedicated APIs scoped to their own client. They can create service requests, add public comments, upload attachments, and view public updates.

## Notification Architecture

Notifications are stored as database rows. Workflow events create notifications synchronously for relevant users, such as:

- technician assignment
- work order status changes
- new client service requests
- client comments
- public work order updates
- overdue work orders

Notification rows are user-specific, so the notification API returns only the authenticated user's notifications.

## Background Task Architecture

Celery handles background work. The local Docker stack includes:

- RabbitMQ as the Celery broker
- Redis as the Celery result backend and cache backend
- Celery worker for task execution
- Celery Beat for periodic scheduling

Implemented task workflows include:

- marking overdue work orders
- generating daily work order summaries

## Report Architecture

Reports are organization-scoped. The reports app provides dashboard totals, work order status/priority summaries, and daily summary data.

Reports aggregate data from clients, assets, memberships, work orders, notifications, and daily summary rows.

## API Schema

OpenAPI schema generation is provided by drf-spectacular. Swagger UI is served at `/api/docs/`.
