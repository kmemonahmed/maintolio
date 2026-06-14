import { cn, titleCase } from "@/lib/utils";

const statusClass: Record<string, string> = {
  OPEN: "border-sky-200 bg-sky-50 text-sky-700",
  ASSIGNED: "border-indigo-200 bg-indigo-50 text-indigo-700",
  IN_PROGRESS: "border-amber-200 bg-amber-50 text-amber-800",
  ON_HOLD: "border-zinc-200 bg-zinc-50 text-zinc-700",
  COMPLETED: "border-emerald-200 bg-emerald-50 text-emerald-700",
  CANCELLED: "border-rose-200 bg-rose-50 text-rose-700",
  OVERDUE: "border-red-200 bg-red-50 text-red-700",
  LOW: "border-slate-200 bg-slate-50 text-slate-700",
  MEDIUM: "border-cyan-200 bg-cyan-50 text-cyan-700",
  HIGH: "border-orange-200 bg-orange-50 text-orange-700",
  URGENT: "border-red-200 bg-red-50 text-red-700",
  OWNER: "border-violet-200 bg-violet-50 text-violet-700",
  ADMIN: "border-blue-200 bg-blue-50 text-blue-700",
  MANAGER: "border-teal-200 bg-teal-50 text-teal-700",
  TECHNICIAN: "border-stone-200 bg-stone-50 text-stone-700",
};

export function Badge({ value, className }: { value?: string | boolean | null; className?: string }) {
  const text = typeof value === "boolean" ? (value ? "Active" : "Inactive") : titleCase(value);
  const key = String(value ?? "").toUpperCase();
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center rounded-full border px-2 text-xs font-medium",
        statusClass[key] ?? "border-border bg-muted text-muted-foreground",
        className,
      )}
    >
      {text}
    </span>
  );
}

