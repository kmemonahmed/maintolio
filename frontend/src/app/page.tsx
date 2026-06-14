"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { LoadingBlock } from "@/components/ui/loading";

export default function Home() {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (auth.isLoading) return;
    if (!auth.user) {
      router.replace("/login");
      return;
    }
    if (auth.isClientContact) router.replace("/client/requests");
    else if (auth.isTechnician) router.replace("/tech/work-orders");
    else router.replace("/app/dashboard");
  }, [auth, router]);

  return <LoadingBlock label="Opening Maintolio" />;
}

