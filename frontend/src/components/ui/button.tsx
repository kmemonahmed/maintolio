import { Slot } from "@radix-ui/react-slot";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "icon";
};

export function Button({ asChild, className, variant = "primary", size = "md", ...props }: ButtonProps) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md border text-sm font-semibold shadow-sm transition disabled:pointer-events-none disabled:opacity-55",
        variant === "primary" && "border-primary bg-primary text-primary-foreground hover:bg-[#095767]",
        variant === "secondary" && "border-border bg-surface text-foreground hover:border-[#b8c8ce] hover:bg-[#f7fafb]",
        variant === "ghost" && "border-transparent bg-transparent text-muted-foreground shadow-none hover:bg-muted hover:text-foreground",
        variant === "danger" && "border-danger bg-danger text-white hover:bg-[#982018]",
        size === "sm" && "h-8 px-3",
        size === "md" && "h-10 px-4",
        size === "icon" && "h-9 w-9",
        className,
      )}
      {...props}
    />
  );
}
