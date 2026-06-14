"use client";

import { AuthGate } from "@/components/auth-gate";
import { AppShell } from "@/components/layout/app-shell";

export default function CompanyLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate mode="company">
      <AppShell mode="company">{children}</AppShell>
    </AuthGate>
  );
}

