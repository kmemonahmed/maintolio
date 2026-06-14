"use client";

import { AuthGate } from "@/components/auth-gate";
import { AppShell } from "@/components/layout/app-shell";

export default function TechnicianLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate mode="technician">
      <AppShell mode="technician">{children}</AppShell>
    </AuthGate>
  );
}

