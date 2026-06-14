"use client";

import { useQuery } from "@tanstack/react-query";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import {
  Bell,
  BriefcaseBusiness,
  Building2,
  ClipboardList,
  HardHat,
  Home,
  LogOut,
  Menu,
  UserCircle,
  Users,
  Wrench,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { cn, mediaUrl } from "@/lib/utils";

const companyNav = [
  { href: "/app/dashboard", label: "Dashboard", icon: Home },
  { href: "/app/work-orders", label: "Work Orders", icon: ClipboardList },
  { href: "/app/clients", label: "Clients", icon: Building2 },
  { href: "/app/client-contacts", label: "Contacts", icon: Users },
  { href: "/app/assets", label: "Assets", icon: Wrench },
  { href: "/app/team", label: "Team", icon: BriefcaseBusiness },
  { href: "/app/profile", label: "Profile", icon: UserCircle },
];

const technicianNav = [
  { href: "/tech/work-orders", label: "Assigned Work", icon: HardHat },
  { href: "/tech/profile", label: "Profile", icon: UserCircle },
];

const clientNav = [
  { href: "/client/requests", label: "Requests", icon: ClipboardList },
  { href: "/client/profile", label: "Profile", icon: UserCircle },
];

function navFor(mode: "company" | "technician" | "client") {
  if (mode === "technician") return technicianNav;
  if (mode === "client") return clientNav;
  return companyNav;
}

export function AppShell({ children, mode }: { children: React.ReactNode; mode: "company" | "technician" | "client" }) {
  const auth = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navItems = navFor(mode);
  const unreadQuery = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: api.unreadCount,
    enabled: Boolean(auth.user),
    refetchInterval: 30000,
  });
  const unreadCount = unreadQuery.data?.unread_count ?? 0;
  const unreadLabel = unreadCount > 99 ? "99+" : String(unreadCount);
  const notificationsHref =
    mode === "client" ? "/client/notifications" : mode === "technician" ? "/tech/notifications" : "/app/notifications";
  const avatar = mediaUrl(auth.user?.avatar);
  const initials = getInitials(auth.user?.full_name || auth.user?.email);

  const sidebar = (
    <aside className="flex h-full w-[17rem] flex-col border-r border-[#20363e] bg-[#102027] text-white">
      <div className="flex h-24 items-center justify-between border-b border-white/10 px-4">
        <Link href={mode === "company" ? "/app/dashboard" : mode === "technician" ? "/tech/work-orders" : "/client/requests"}>
          <span className="flex h-20 w-[14.5rem] items-center overflow-hidden rounded-lg bg-white shadow-lg shadow-cyan-950/20 ring-1 ring-white/10">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/maintolio-logo.svg" alt="Maintolio" className="h-[4.7rem] w-full object-cover object-center" />
          </span>
        </Link>
        <button className="md:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation">
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-[#b8d0d6] transition hover:bg-white/8 hover:text-white",
                active && "bg-[#e4f3f5] text-[#0e5c6d] shadow-sm",
              )}
              onClick={() => setMobileOpen(false)}
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1">{item.label}</span>
              {item.href === notificationsHref && unreadCount > 0 ? (
                <span className="min-w-5 rounded-full bg-[#23a3b8] px-1.5 py-0.5 text-center text-[11px] font-bold leading-4 text-white">
                  {unreadLabel}
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-white/10 p-3 text-xs font-semibold uppercase tracking-[0.16em] text-[#6f929a]">Maintolio</div>
    </aside>
  );

  return (
    <div className="app-canvas min-h-screen">
      <div className="fixed inset-y-0 left-0 z-30 hidden md:block">{sidebar}</div>
      {mobileOpen ? <div className="fixed inset-0 z-40 bg-black/30 md:hidden" onClick={() => setMobileOpen(false)} /> : null}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 transition md:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {sidebar}
      </div>

      <div className="md:pl-[17rem]">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-white/88 px-4 backdrop-blur-xl md:px-6">
          <Button variant="ghost" size="icon" className="shrink-0 md:hidden" onClick={() => setMobileOpen(true)}>
            <Menu className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium uppercase text-muted-foreground">
              {mode === "company" ? auth.selectedMembership?.organization.name : mode === "technician" ? "Technician Portal" : "Client Portal"}
            </p>
            <h1 className="truncate text-base font-semibold">Service operations workspace</h1>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <Link href={notificationsHref} className="relative rounded-md border border-border bg-surface p-2 shadow-sm hover:bg-muted" aria-label="Notifications">
              <Bell className="h-5 w-5" />
              {unreadCount > 0 ? (
                <span className="absolute -right-2 -top-2 min-w-5 rounded-full border-2 border-white bg-danger px-1 text-center text-[11px] font-bold leading-4 text-white">
                  {unreadLabel}
                </span>
              ) : null}
            </Link>
            <DropdownMenu.Root modal={false}>
              <DropdownMenu.Trigger asChild>
                <button
                  className="flex h-10 w-10 cursor-pointer items-center justify-center overflow-hidden rounded-full border border-[#9fc8d1] bg-[#e4f3f5] text-sm font-semibold text-primary shadow-sm outline outline-2 outline-offset-0 outline-primary ring-2 ring-[#d4eef3] transition hover:border-primary hover:bg-muted"
                  aria-label="Open profile menu"
                >
                  {avatar ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={avatar} alt="" className="h-full w-full object-cover" />
                  ) : (
                    initials
                  )}
                </button>
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  align="end"
                  sideOffset={8}
                  className="z-50 w-48 rounded-lg border border-border bg-surface p-1.5 shadow-xl shadow-slate-950/15"
                >
                  <div className="rounded-md bg-[#f8fbfc] px-2 py-1.5">
                    <p className="truncate text-sm font-semibold">{auth.user?.full_name || "Profile"}</p>
                    <p className="mt-1 truncate text-xs text-muted-foreground">{auth.user?.email}</p>
                  </div>
                  <DropdownMenu.Item asChild>
                    <button
                      type="button"
                      className="mt-1.5 flex h-8 w-full items-center justify-start gap-2 rounded-md border border-rose-200 bg-rose-50 px-2.5 text-left text-xs font-semibold text-danger shadow-sm hover:bg-rose-100"
                      onClick={() => void auth.logout()}
                    >
                      <LogOut className="h-4 w-4" />
                      Sign out
                    </button>
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </div>
        </header>
        <main className="mx-auto w-full max-w-7xl px-4 py-7 md:px-7">{children}</main>
      </div>
    </div>
  );
}

function getInitials(value?: string | null) {
  if (!value) return "U";
  const parts = value.trim().split(/\s+/).filter(Boolean);
  const first = parts[0]?.[0] ?? "U";
  const second = parts.length > 1 ? parts[parts.length - 1]?.[0] : "";
  return `${first}${second}`.toUpperCase();
}
