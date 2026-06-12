# API Overview

Maintolio exposes a role-aware REST API for company users, technicians, and client contacts. All company-side resources are scoped to the authenticated user's active organization membership. Client portal resources are scoped to the authenticated client contact's client.

## API Groups

| Group | Base path | Primary users |
| --- | --- | --- |
| Auth | `/api/auth/` | All users |
| Organizations | `/api/organizations/` | OWNER, ADMIN |
| Team Members | `/api/team-members/` | OWNER, ADMIN, MANAGER read access |
| Clients | `/api/clients/` | OWNER, ADMIN, MANAGER |
| Client Contacts | `/api/client-contacts/` | OWNER, ADMIN, MANAGER |
| Assets | `/api/assets/` | OWNER, ADMIN, MANAGER |
| Work Orders | `/api/work-orders/` | OWNER, ADMIN, MANAGER, assigned TECHNICIAN for selected actions |
| Technician Portal | `/api/technician/` | TECHNICIAN |
| Client Portal | `/api/client-portal/` | Client Contact |
| Notifications | `/api/notifications/` | Authenticated users |
| Reports | `/api/reports/` | OWNER, ADMIN, MANAGER |
| Swagger | `/api/docs/` | Developers |

## Main Endpoints

### Auth

- `POST /api/auth/register/`: register a new organization and owner user.
- `POST /api/auth/login/`: obtain JWT tokens.
- `POST /api/auth/token/refresh/`: refresh access token.
- `GET /api/auth/me/`: retrieve current user profile.
- `POST /api/auth/change-password/`: change password.
- `POST /api/auth/logout/`: blacklist refresh token.

### Organization and Team

- `GET /api/organizations/current/`: current organization and membership context.
- `PATCH /api/organizations/current/`: update organization profile.
- `GET /api/team-members/`: list team members.
- `POST /api/team-members/`: invite/create team member.
- `PATCH /api/team-members/{id}/`: update member details or role.
- `DELETE /api/team-members/{id}/`: soft-deactivate a team member.

### Clients and Contacts

- `GET /api/clients/`: list clients.
- `POST /api/clients/`: create client.
- `GET /api/clients/{id}/`: retrieve client.
- `PATCH /api/clients/{id}/`: update client.
- `DELETE /api/clients/{id}/`: soft-deactivate client.
- `GET /api/client-contacts/`: list contacts.
- `POST /api/client-contacts/`: create contact.
- `PATCH /api/client-contacts/{id}/`: update contact.
- `DELETE /api/client-contacts/{id}/`: soft-deactivate contact.

### Assets

- `GET /api/assets/`: list assets.
- `POST /api/assets/`: create asset.
- `GET /api/assets/{id}/`: retrieve asset.
- `PATCH /api/assets/{id}/`: update asset.
- `DELETE /api/assets/{id}/`: retire asset.
- `GET /api/assets/by-client/{client_id}/`: list assets for a client.

### Work Orders

- `GET /api/work-orders/`: list work orders.
- `POST /api/work-orders/`: create work order.
- `GET /api/work-orders/{id}/`: retrieve work order.
- `PATCH /api/work-orders/{id}/`: update work order.
- `DELETE /api/work-orders/{id}/`: cancel work order.
- `POST /api/work-orders/{id}/assign/`: assign technician.
- `POST /api/work-orders/{id}/change-status/`: change status.
- `POST /api/work-orders/{id}/add-update/`: add update/comment.
- `POST /api/work-orders/{id}/upload-attachment/`: upload attachment.
- `GET /api/work-orders/{id}/updates/`: list updates.
- `GET /api/work-orders/{id}/attachments/`: list attachments.

### Technician Portal

- `GET /api/technician/work-orders/`: list assigned work orders.
- `GET /api/technician/work-orders/{id}/`: retrieve assigned work order.

### Client Portal

- `GET /api/client-portal/requests/`: list own client's requests.
- `POST /api/client-portal/requests/`: create service request.
- `GET /api/client-portal/requests/{id}/`: retrieve own client's request.
- `POST /api/client-portal/requests/{id}/add-comment/`: add public comment.
- `POST /api/client-portal/requests/{id}/upload-attachment/`: upload attachment.
- `GET /api/client-portal/requests/{id}/updates/`: list public updates.
- `GET /api/client-portal/requests/{id}/attachments/`: list attachments.

### Notifications

- `GET /api/notifications/`: list current user's notifications.
- `GET /api/notifications/{id}/`: retrieve notification.
- `POST /api/notifications/{id}/mark-read/`: mark as read.
- `POST /api/notifications/{id}/mark-unread/`: mark as unread.
- `POST /api/notifications/mark-all-read/`: mark all current user's notifications as read.
- `GET /api/notifications/unread-count/`: unread notification count.

### Reports

- `GET /api/reports/dashboard-summary/`: dashboard totals.
- `GET /api/reports/work-order-summary/`: status and priority summary.
- `GET /api/reports/daily-work-order-summary/`: daily work order summary.

## Workflow Examples

### Company Work Order Flow

1. OWNER/ADMIN/MANAGER creates a client.
2. OWNER/ADMIN/MANAGER creates client assets.
3. OWNER/ADMIN/MANAGER creates a work order.
4. Manager assigns a technician.
5. Technician changes status and adds updates.
6. Managers and relevant users receive notifications.
7. Reports reflect updated work order counts.

### Client Service Request Flow

1. Client contact logs in.
2. Client contact creates a request through `/api/client-portal/requests/`.
3. Company users see the new request.
4. Manager assigns a technician.
5. Public technician/company updates are visible to the client contact.
6. Internal updates remain hidden from the client portal.

### Technician Flow

1. Technician logs in.
2. Technician lists assigned work orders through `/api/technician/work-orders/`.
3. Technician opens a work order, changes status, and adds updates.
4. Company users and clients receive relevant notifications.

## Filtering, Search, Ordering, and Pagination

Main list endpoints support DRF-native filtering, search, ordering, and page-number pagination. Example:

```text
/api/work-orders/?status=OPEN&priority=HIGH&search=pump&ordering=-due_date&page=1
```
