"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { KeyRound } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";

const passwordSchema = z
  .object({
    old_password: z.string().min(1, "Enter your current password."),
    new_password: z.string().min(8, "Choose a stronger password with at least 8 characters."),
    new_password_confirm: z.string().min(8, "Confirm the new password before saving."),
  })
  .refine((data) => data.new_password === data.new_password_confirm, {
    path: ["new_password_confirm"],
    message: "The confirmation does not match the new password.",
  });

export function SettingsPage() {
  const auth = useAuth();
  const form = useForm<z.infer<typeof passwordSchema>>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { old_password: "", new_password: "", new_password_confirm: "" },
  });
  const mutation = useMutation({
    mutationFn: api.changePassword,
    onSuccess: () => {
      toast.success("Password updated");
      form.reset();
    },
    onError: () => toast.error("We could not update the password. Please check the current password and try again."),
  });

  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">Account control</p>
        <h2 className="mt-1 text-3xl font-semibold tracking-tight">Settings</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Review your workspace identity and keep account access secure.</p>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="premium-panel border-[#d7e3e7]">
          <CardHeader>
            <h3 className="font-semibold">Current profile</h3>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Info label="Name" value={auth.user?.full_name || "Not set"} />
            <Info label="Email" value={auth.user?.email || "Not set"} />
            <Info label="Role" value={auth.role || "User"} />
            <Info label="Organization" value={auth.selectedMembership?.organization.name ?? auth.user?.client_contact_profile?.client_name ?? "None"} />
          </CardContent>
        </Card>
        <Card className="premium-panel border-[#d7e3e7]">
          <CardHeader>
            <div className="flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-primary" />
              <h3 className="font-semibold">Change password</h3>
            </div>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
              <Field label="Current password" error={form.formState.errors.old_password?.message}>
                <Input type="password" {...form.register("old_password")} />
              </Field>
              <Field label="New password" error={form.formState.errors.new_password?.message}>
                <Input type="password" {...form.register("new_password")} />
              </Field>
              <Field label="Confirm new password" error={form.formState.errors.new_password_confirm?.message}>
                <Input type="password" {...form.register("new_password_confirm")} />
              </Field>
              <Button disabled={mutation.isPending}>{mutation.isPending ? "Updating" : "Update password"}</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-[#fbfcfd] p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {error ? <p className="text-xs text-danger">{error}</p> : null}
    </div>
  );
}
