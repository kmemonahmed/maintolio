"use client";

import { AuthGate } from "@/components/auth-gate";
import { AppShell } from "@/components/layout/app-shell";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate mode="client">
      <AppShell mode="client">{children}</AppShell>
    </AuthGate>
  );
}

