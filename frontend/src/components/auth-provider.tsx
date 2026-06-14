"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import {
  clearTokens,
  getSelectedOrganizationId,
  getTokens,
  setSelectedOrganizationId,
  setTokens,
} from "@/lib/auth-storage";
import type { Me, Membership, Role } from "@/lib/types";

type AuthContextValue = {
  user: Me | null;
  isLoading: boolean;
  selectedMembership: Membership | null;
  selectedOrganizationId: string | null;
  role: Role | "CLIENT" | null;
  isCompanyUser: boolean;
  isTechnician: boolean;
  isClientContact: boolean;
  canManage: boolean;
  canAdministerWorkspace: boolean;
  login: (body: { email: string; password: string }) => Promise<void>;
  register: (body: Record<string, unknown>) => Promise<void>;
  logout: () => Promise<void>;
  setOrganization: (id: string) => void;
  refetchMe: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function defaultRouteFor(user: Me, role: AuthContextValue["role"]) {
  if (role === "CLIENT" || user.client_contact_profile) return "/client/requests";
  if (role === "TECHNICIAN") return "/tech/work-orders";
  return "/app/dashboard";
}

function resolveMembership(user: Me | null, selectedId: string | null) {
  if (!user?.organization_memberships.length) return null;
  return (
    user.organization_memberships.find((membership) => membership.organization.id === selectedId) ??
    user.organization_memberships[0]
  );
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError && typeof error.detail === "object" && error.detail) {
    const first = Object.values(error.detail as Record<string, unknown>)[0];
    return Array.isArray(first) ? String(first[0]) : String(first);
  }
  return error instanceof Error ? error.message : "We could not complete that request. Please try again.";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [selectedOrganizationId, setSelectedOrgState] = useState<string | null>(() => getSelectedOrganizationId());
  const hasTokens = typeof window !== "undefined" ? Boolean(getTokens()) : false;

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    enabled: hasTokens,
  });

  useEffect(() => {
    if (meQuery.error instanceof ApiError && meQuery.error.status === 401) {
      clearTokens();
      router.replace("/login");
    }
  }, [meQuery.error, router]);

  useEffect(() => {
    if (!meQuery.data?.is_platform_admin) return;

    clearTokens();
    queryClient.clear();
    toast.error("You are not authorized to access this portal.");
    router.replace("/login");
  }, [meQuery.data?.is_platform_admin, queryClient, router]);

  const selectedMembership = useMemo(
    () => resolveMembership(meQuery.data ?? null, selectedOrganizationId),
    [meQuery.data, selectedOrganizationId],
  );

  const role = selectedMembership?.role ?? (meQuery.data?.client_contact_profile ? "CLIENT" : null);
  const isClientContact = role === "CLIENT";
  const isTechnician = role === "TECHNICIAN";
  const isCompanyUser = role === "OWNER" || role === "ADMIN" || role === "MANAGER";
  const canManage = role === "OWNER" || role === "ADMIN" || role === "MANAGER";
  const canAdministerWorkspace = role === "OWNER" || role === "ADMIN";

  const loginMutation = useMutation({
    mutationFn: api.login,
    onSuccess: async (tokens) => {
      setTokens(tokens);
      const user = await queryClient.fetchQuery({ queryKey: ["me"], queryFn: api.me });
      const membership = resolveMembership(user, getSelectedOrganizationId());
      if (membership) {
        setSelectedOrganizationId(membership.organization.id);
        setSelectedOrgState(membership.organization.id);
      }
      router.replace(defaultRouteFor(user, membership?.role ?? (user.client_contact_profile ? "CLIENT" : null)));
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const registerMutation = useMutation({
    mutationFn: api.register,
    onSuccess: async (tokens) => {
      setTokens(tokens);
      const user = await queryClient.fetchQuery({ queryKey: ["me"], queryFn: api.me });
      const membership = resolveMembership(user, null);
      if (membership) {
        setSelectedOrganizationId(membership.organization.id);
        setSelectedOrgState(membership.organization.id);
      }
      router.replace("/app/dashboard");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  async function logout() {
    const tokens = getTokens();
    try {
      if (tokens?.refresh) await api.logout(tokens.refresh);
    } catch {
      // Local token cleanup is enough if the refresh token is already invalid.
    }
    clearTokens();
    setSelectedOrganizationId(null);
    setSelectedOrgState(null);
    queryClient.clear();
    router.replace("/login");
  }

  function setOrganization(id: string) {
    setSelectedOrganizationId(id);
    setSelectedOrgState(id);
    queryClient.invalidateQueries();
  }

  useEffect(() => {
    const isPublic = pathname === "/" || pathname.startsWith("/login") || pathname.startsWith("/register");
    if (!hasTokens && !isPublic) router.replace("/login");
  }, [hasTokens, pathname, router]);

  const value: AuthContextValue = {
    user: meQuery.data ?? null,
    isLoading: meQuery.isLoading,
    selectedMembership,
    selectedOrganizationId,
    role,
    isCompanyUser,
    isTechnician,
    isClientContact,
    canManage,
    canAdministerWorkspace,
    login: async (body) => {
      try {
        await loginMutation.mutateAsync(body);
      } catch {
        // The mutation onError already shows the portal-safe message.
      }
    },
    register: async (body) => {
      try {
        await registerMutation.mutateAsync(body);
      } catch {
        // The mutation onError already shows the portal-safe message.
      }
    },
    logout,
    setOrganization,
    refetchMe: () => {
      void meQuery.refetch();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
