"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bell,
  BriefcaseBusiness,
  Building2,
  ClipboardList,
  HardHat,
  Home,
  LogOut,
  Menu,
  Settings,
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
import { cn } from "@/lib/utils";

const companyNav = [
  { href: "/app/dashboard", label: "Dashboard", icon: Home },
  { href: "/app/work-orders", label: "Work Orders", icon: ClipboardList },
  { href: "/app/clients", label: "Clients", icon: Building2 },
  { href: "/app/client-contacts", label: "Contacts", icon: Users },
  { href: "/app/assets", label: "Assets", icon: Wrench },
  { href: "/app/team", label: "Team", icon: BriefcaseBusiness },
  { href: "/app/settings", label: "Settings", icon: Settings },
];

const technicianNav = [
  { href: "/tech/work-orders", label: "Assigned Work", icon: HardHat },
  { href: "/tech/settings", label: "Settings", icon: Settings },
];

const clientNav = [
  { href: "/client/requests", label: "Requests", icon: ClipboardList },
  { href: "/client/settings", label: "Settings", icon: Settings },
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

  const sidebar = (
    <aside className="flex h-full w-[17rem] flex-col border-r border-[#20363e] bg-[#102027] text-white">
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-5">
        <Link href={mode === "company" ? "/app/dashboard" : mode === "technician" ? "/tech/work-orders" : "/client/requests"}>
          <span className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#23a3b8] shadow-lg shadow-cyan-950/30">
              <Building2 className="h-4 w-4" />
            </span>
            <span>
              <span className="block text-lg font-semibold tracking-tight">Maintolio</span>
              <span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-[#9bcbd4]">Operations</span>
            </span>
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

      <div className="border-t border-white/10 p-3">
        <Button className="w-full justify-start text-[#b8d0d6] hover:bg-white/8 hover:text-white" variant="ghost" onClick={() => void auth.logout()}>
          <LogOut className="h-4 w-4" />
          Sign out
        </Button>
      </div>
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
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-white/88 px-4 backdrop-blur-xl md:px-6">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileOpen(true)}>
            <Menu className="h-5 w-5" />
          </Button>
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">
              {mode === "company" ? auth.selectedMembership?.organization.name : mode === "technician" ? "Technician Portal" : "Client Portal"}
            </p>
            <h1 className="text-base font-semibold">Service operations workspace</h1>
          </div>
          <Link href={notificationsHref} className="relative rounded-md border border-border bg-surface p-2 shadow-sm hover:bg-muted" aria-label="Notifications">
            <Bell className="h-5 w-5" />
            {unreadCount > 0 ? (
              <span className="absolute -right-2 -top-2 min-w-5 rounded-full border-2 border-white bg-danger px-1 text-center text-[11px] font-bold leading-4 text-white">
                {unreadLabel}
              </span>
            ) : null}
          </Link>
        </header>
        <main className="mx-auto w-full max-w-7xl px-4 py-7 md:px-7">{children}</main>
      </div>
    </div>
  );
}
