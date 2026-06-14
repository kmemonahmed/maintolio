import { clearTokens, getSelectedOrganizationId, getTokens, setTokens } from "@/lib/auth-storage";
import type {
  Asset,
  Attachment,
  Client,
  ClientContact,
  DailyWorkOrderSummary,
  DashboardSummary,
  Me,
  NotificationItem,
  PaginatedResponse,
  TeamMember,
  WorkOrder,
  WorkOrderListItem,
  WorkOrderSummary,
  WorkOrderUpdate,
} from "@/lib/types";
import { compactObject } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  organizationId?: string | null;
  isFormData?: boolean;
  retry?: boolean;
};

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(readableApiMessage(detail));
    this.status = status;
    this.detail = detail;
  }
}

function readableApiMessage(detail: unknown) {
  if (typeof detail === "string") return detail;

  if (detail && typeof detail === "object") {
    const value = (detail as Record<string, unknown>).detail;
    if (typeof value === "string") return value;

    const first = Object.values(detail as Record<string, unknown>)[0];
    if (typeof first === "string") return first;
    if (Array.isArray(first) && first.length) return String(first[0]);
  }

  return "We could not complete that request. Please try again.";
}

function buildUrl(path: string, params?: Record<string, unknown>) {
  const base =
    typeof window !== "undefined"
      ? window.location.origin
      : "http://127.0.0.1:3000";
  const url = new URL(path.startsWith("http") ? path : `${API_BASE_URL}${path}`, base);
  Object.entries(compactObject(params ?? {})).forEach(([key, value]) => {
    url.searchParams.set(key, String(value));
  });
  return url.toString();
}

async function refreshAccessToken() {
  const tokens = getTokens();
  if (!tokens?.refresh) return false;

  const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: tokens.refresh }),
  });

  if (!response.ok) {
    clearTokens();
    return false;
  }

  const data = (await response.json()) as { access: string; refresh?: string };
  setTokens({ access: data.access, refresh: data.refresh ?? tokens.refresh });
  return true;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const tokens = getTokens();
  const headers = new Headers(options.headers);

  if (!options.isFormData) {
    headers.set("Content-Type", "application/json");
  }

  if (tokens?.access) {
    headers.set("Authorization", `Bearer ${tokens.access}`);
  }

  const organizationId = options.organizationId ?? getSelectedOrganizationId();
  if (organizationId) {
    headers.set("X-Organization-ID", organizationId);
  }

  const response = await fetch(buildUrl(path), {
    ...options,
    headers,
    body: options.isFormData ? (options.body as BodyInit) : options.body ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 401 && options.retry !== false && (await refreshAccessToken())) {
    return apiRequest<T>(path, { ...options, retry: false });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }

  return data as T;
}

export const api = {
  login: (body: { email: string; password: string }) =>
    apiRequest<{ access: string; refresh: string }>("/api/auth/login/", { method: "POST", body }),
  register: (body: Record<string, unknown>) =>
    apiRequest<{ access: string; refresh: string; user: { id: string; email: string; full_name: string } }>(
      "/api/auth/register/",
      { method: "POST", body },
    ),
  me: () => apiRequest<Me>("/api/auth/me/"),
  logout: (refresh: string) => apiRequest<{ message: string }>("/api/auth/logout/", { method: "POST", body: { refresh } }),
  changePassword: (body: { old_password: string; new_password: string; new_password_confirm: string }) =>
    apiRequest<{ message: string }>("/api/auth/change-password/", { method: "POST", body }),

  listClients: (params?: Record<string, unknown>) => apiRequest<PaginatedResponse<Client>>(buildUrl("/api/clients/", params)),
  createClient: (body: Record<string, unknown>) => apiRequest<Client>("/api/clients/", { method: "POST", body }),
  updateClient: (id: string, body: Record<string, unknown>) => apiRequest<Client>(`/api/clients/${id}/`, { method: "PATCH", body }),
  deleteClient: (id: string) => apiRequest<void>(`/api/clients/${id}/`, { method: "DELETE" }),

  listContacts: (params?: Record<string, unknown>) => apiRequest<PaginatedResponse<ClientContact>>(buildUrl("/api/client-contacts/", params)),
  createContact: (body: Record<string, unknown>) => apiRequest<ClientContact>("/api/client-contacts/", { method: "POST", body }),
  updateContact: (id: string, body: Record<string, unknown>) =>
    apiRequest<ClientContact>(`/api/client-contacts/${id}/`, { method: "PATCH", body }),
  deleteContact: (id: string) => apiRequest<void>(`/api/client-contacts/${id}/`, { method: "DELETE" }),

  listAssets: (params?: Record<string, unknown>) => apiRequest<PaginatedResponse<Asset>>(buildUrl("/api/assets/", params)),
  createAsset: (body: Record<string, unknown>) => apiRequest<Asset>("/api/assets/", { method: "POST", body }),
  updateAsset: (id: string, body: Record<string, unknown>) => apiRequest<Asset>(`/api/assets/${id}/`, { method: "PATCH", body }),
  deleteAsset: (id: string) => apiRequest<void>(`/api/assets/${id}/`, { method: "DELETE" }),

  listTeam: (params?: Record<string, unknown>) => apiRequest<PaginatedResponse<TeamMember>>(buildUrl("/api/team-members/", params)),
  createTeamMember: (body: Record<string, unknown>) => apiRequest<TeamMember>("/api/team-members/", { method: "POST", body }),
  updateTeamMember: (id: string, body: Record<string, unknown>) =>
    apiRequest<TeamMember>(`/api/team-members/${id}/`, { method: "PATCH", body }),
  deleteTeamMember: (id: string) => apiRequest<void>(`/api/team-members/${id}/`, { method: "DELETE" }),

  listWorkOrders: (params?: Record<string, unknown>) => apiRequest<PaginatedResponse<WorkOrderListItem>>(buildUrl("/api/work-orders/", params)),
  getWorkOrder: (id: string) => apiRequest<WorkOrder>(`/api/work-orders/${id}/`),
  createWorkOrder: (body: Record<string, unknown>) => apiRequest<WorkOrderListItem>("/api/work-orders/", { method: "POST", body }),
  updateWorkOrder: (id: string, body: Record<string, unknown>) => apiRequest<WorkOrder>(`/api/work-orders/${id}/`, { method: "PATCH", body }),
  cancelWorkOrder: (id: string) => apiRequest<void>(`/api/work-orders/${id}/`, { method: "DELETE" }),
  assignWorkOrder: (id: string, body: { assigned_to: string; message?: string }) =>
    apiRequest<WorkOrderListItem>(`/api/work-orders/${id}/assign/`, { method: "POST", body }),
  changeWorkOrderStatus: (id: string, body: { status: string; message?: string; is_internal?: boolean }) =>
    apiRequest<WorkOrderListItem>(`/api/work-orders/${id}/change-status/`, { method: "POST", body }),
  addWorkOrderUpdate: (id: string, body: { message: string; is_internal?: boolean }) =>
    apiRequest<WorkOrderUpdate>(`/api/work-orders/${id}/add-update/`, { method: "POST", body }),
  listWorkOrderUpdates: (id: string) => apiRequest<WorkOrderUpdate[]>(`/api/work-orders/${id}/updates/`),
  listWorkOrderAttachments: (id: string) => apiRequest<Attachment[]>(`/api/work-orders/${id}/attachments/`),
  uploadWorkOrderAttachment: (id: string, body: FormData) =>
    apiRequest<Attachment>(`/api/work-orders/${id}/upload-attachment/`, { method: "POST", body, isFormData: true }),

  listTechnicianWorkOrders: (params?: Record<string, unknown>) =>
    apiRequest<PaginatedResponse<WorkOrderListItem>>(buildUrl("/api/technician/work-orders/", params)),
  getTechnicianWorkOrder: (id: string) => apiRequest<WorkOrder>(`/api/technician/work-orders/${id}/`),

  listClientRequests: (params?: Record<string, unknown>) =>
    apiRequest<PaginatedResponse<WorkOrderListItem>>(buildUrl("/api/client-portal/requests/", params)),
  getClientRequest: (id: string) => apiRequest<WorkOrder>(`/api/client-portal/requests/${id}/`),
  createClientRequest: (body: Record<string, unknown>) =>
    apiRequest<WorkOrderListItem>("/api/client-portal/requests/", { method: "POST", body }),
  addClientComment: (id: string, body: { message: string }) =>
    apiRequest<WorkOrderUpdate>(`/api/client-portal/requests/${id}/add-comment/`, { method: "POST", body }),
  listClientRequestUpdates: (id: string) => apiRequest<WorkOrderUpdate[]>(`/api/client-portal/requests/${id}/updates/`),
  listClientRequestAttachments: (id: string) => apiRequest<Attachment[]>(`/api/client-portal/requests/${id}/attachments/`),
  uploadClientRequestAttachment: (id: string, body: FormData) =>
    apiRequest<Attachment>(`/api/client-portal/requests/${id}/upload-attachment/`, { method: "POST", body, isFormData: true }),

  listNotifications: (params?: Record<string, unknown>) =>
    apiRequest<PaginatedResponse<NotificationItem>>(buildUrl("/api/notifications/", params)),
  markNotificationRead: (id: string) => apiRequest<NotificationItem>(`/api/notifications/${id}/mark-read/`, { method: "POST" }),
  markNotificationUnread: (id: string) =>
    apiRequest<NotificationItem>(`/api/notifications/${id}/mark-unread/`, { method: "POST" }),
  markAllNotificationsRead: () => apiRequest<{ updated_count: number }>("/api/notifications/mark-all-read/", { method: "POST" }),
  unreadCount: () => apiRequest<{ unread_count: number }>("/api/notifications/unread-count/"),

  dashboardSummary: () => apiRequest<DashboardSummary>("/api/reports/dashboard-summary/"),
  workOrderSummary: (params?: Record<string, unknown>) => apiRequest<WorkOrderSummary>(buildUrl("/api/reports/work-order-summary/", params)),
  dailyWorkOrderSummary: (params?: Record<string, unknown>) =>
    apiRequest<DailyWorkOrderSummary>(buildUrl("/api/reports/daily-work-order-summary/", params)),
};
