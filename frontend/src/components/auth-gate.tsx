"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/components/auth-provider";

type GateMode = "company" | "technician" | "client" | "authenticated";

export function AuthGate({ children, mode }: { children: React.ReactNode; mode: GateMode }) {
  const auth = useAuth();
  const router = useRouter();
  const redirectPath =
    !auth.isLoading && auth.user
      ? mode === "company" && !auth.isCompanyUser
        ? auth.isClientContact
          ? "/client/requests"
          : "/tech/work-orders"
        : mode === "technician" && !auth.isTechnician
          ? auth.isClientContact
            ? "/client/requests"
            : "/app/dashboard"
          : mode === "client" && !auth.isClientContact
            ? auth.isTechnician
              ? "/tech/work-orders"
              : "/app/dashboard"
            : null
      : null;

  useEffect(() => {
    if (redirectPath) router.replace(redirectPath);
  }, [redirectPath, router]);

  if (auth.isLoading || !auth.user || redirectPath) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return children;
}
