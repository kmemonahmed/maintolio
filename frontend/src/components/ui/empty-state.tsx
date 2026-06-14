import { SearchX } from "lucide-react";

export function EmptyState({ title = "Nothing to show yet", message }: { title?: string; message?: string }) {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed border-[#cbd9dd] bg-[#fbfcfd] p-8 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#e4f3f5] text-primary">
        <SearchX className="h-6 w-6" />
      </div>
      <h3 className="text-sm font-semibold">{title}</h3>
      {message ? <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p> : null}
    </div>
  );
}
