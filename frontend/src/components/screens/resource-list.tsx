"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm";
import { EmptyState } from "@/components/ui/empty-state";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { LoadingBlock } from "@/components/ui/loading";
import type { PaginatedResponse } from "@/lib/types";
import { compactObject, formatDate } from "@/lib/utils";

export type FieldConfig = {
  name: string;
  label: string;
  type?: "text" | "email" | "password" | "textarea" | "select" | "checkbox" | "date" | "datetime-local";
  required?: boolean;
  options?: Array<{ value: string; label: string }>;
  createOnly?: boolean;
};

export type ColumnConfig<T> = {
  header: string;
  value: (row: T) => React.ReactNode;
};

type ResourceListProps<T extends { id: string }> = {
  title: string;
  description: string;
  queryKey: string;
  list: (params: Record<string, unknown>) => Promise<PaginatedResponse<T>>;
  create?: (body: Record<string, unknown>) => Promise<unknown>;
  update?: (id: string, body: Record<string, unknown>) => Promise<unknown>;
  remove?: (id: string) => Promise<unknown>;
  columns: ColumnConfig<T>[];
  fields?: FieldConfig[];
  searchPlaceholder?: string;
  filters?: FieldConfig[];
  getInitialValues?: (row?: T) => Record<string, unknown>;
  getRowHref?: (row: T) => string;
  destructiveLabel?: string;
  actionLabel?: string;
};

export function ResourceList<T extends { id: string }>({
  title,
  description,
  queryKey,
  list,
  create,
  update,
  remove,
  columns,
  fields = [],
  searchPlaceholder = "Search",
  filters = [],
  getInitialValues,
  getRowHref,
  destructiveLabel = "Deactivate",
  actionLabel,
}: ResourceListProps<T>) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [editing, setEditing] = useState<T | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<T | null>(null);

  const params = useMemo(() => compactObject({ page, search, ...filterValues }), [page, search, filterValues]);
  const query = useQuery({ queryKey: [queryKey, params], queryFn: () => list(params) });
  const hasRowActions = Boolean(update || remove);

  const saveMutation = useMutation({
    mutationFn: (body: Record<string, unknown>) => {
      if (editing && update) return update(editing.id, body);
      if (create) return create(body);
      return Promise.resolve();
    },
    onSuccess: () => {
      toast.success(editing ? "Changes saved" : "Record created");
      setFormOpen(false);
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: [queryKey] });
    },
    onError: () => toast.error("We could not save those changes. Please review the details and try again."),
  });

  const deleteMutation = useMutation({
    mutationFn: (row: T) => remove?.(row.id) ?? Promise.resolve(),
    onSuccess: () => {
      toast.success(`${destructiveLabel} complete`);
      setPendingDelete(null);
      queryClient.invalidateQueries({ queryKey: [queryKey] });
    },
    onError: () => toast.error("We could not complete that action. Please try again."),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">Workspace</p>
          <h2 className="mt-1 text-3xl font-semibold tracking-tight">{title}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
        {create ? (
          <Button
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            <Plus className="h-4 w-4" />
            {actionLabel ?? `Add ${title.replace(/s$/, "")}`}
          </Button>
        ) : null}
      </div>

      <Card className="premium-panel border-[#d7e3e7]">
        <CardHeader>
          <div className="grid gap-3 md:grid-cols-[1fr_repeat(3,minmax(150px,220px))]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder={searchPlaceholder}
                value={search}
                onChange={(event) => {
                  setPage(1);
                  setSearch(event.target.value);
                }}
              />
            </div>
            {filters.map((filter) => (
              <Select
                key={filter.name}
                value={filterValues[filter.name] ?? ""}
                onChange={(event) => {
                  setPage(1);
                  setFilterValues((current) => ({ ...current, [filter.name]: event.target.value }));
                }}
              >
                <option value="">{filter.label}</option>
                {filter.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            ))}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {query.isLoading ? (
            <LoadingBlock />
          ) : !query.data?.results.length ? (
            <div className="p-5">
              <EmptyState title="No matching records" message="Adjust your search or filters to widen the view." />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-[#f4f8f9] text-xs uppercase text-muted-foreground">
                  <tr>
                    {columns.map((column) => (
                      <th key={column.header} className="px-4 py-3 font-semibold">
                        {column.header}
                      </th>
                    ))}
                    {hasRowActions ? <th className="w-24 px-4 py-3 text-right font-semibold">Actions</th> : null}
                  </tr>
                </thead>
                <tbody>
                  {query.data.results.map((row) => (
                    <tr key={row.id} className="border-t border-border bg-white transition hover:bg-[#f8fbfc]">
                      {columns.map((column) => (
                        <td key={column.header} className="px-4 py-3 align-middle">
                          {getRowHref && column === columns[0] ? (
                            <a className="font-medium text-primary hover:underline" href={getRowHref(row)}>
                              {column.value(row)}
                            </a>
                          ) : (
                            column.value(row)
                          )}
                        </td>
                      ))}
                      {hasRowActions ? (
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-1">
                            {update ? (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => {
                                  setEditing(row);
                                  setFormOpen(true);
                                }}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                            ) : null}
                            {remove ? (
                              <Button variant="ghost" size="icon" onClick={() => setPendingDelete(row)}>
                                <Trash2 className="h-4 w-4 text-danger" />
                              </Button>
                            ) : null}
                          </div>
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex items-center justify-between border-t border-border bg-[#fbfcfd] px-5 py-3 text-sm text-muted-foreground">
            <span>{query.data ? `${query.data.count} total` : "Loading workspace data"}</span>
            <div className="flex gap-2">
              <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
                Previous
              </Button>
              <Button variant="secondary" size="sm" disabled={!query.data?.next} onClick={() => setPage((value) => value + 1)}>
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {formOpen ? (
        <FormPanel
          title={editing ? `Update ${title}` : actionLabel ?? `Add ${title.replace(/s$/, "")}`}
          fields={fields.filter((field) => !(editing && field.createOnly))}
          initialValues={getInitialValues?.(editing ?? undefined) ?? {}}
          onCancel={() => {
            setFormOpen(false);
            setEditing(null);
          }}
          onSubmit={(values) => saveMutation.mutate(values)}
          isSaving={saveMutation.isPending}
        />
      ) : null}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={`${destructiveLabel} entry`}
        description="This keeps historical activity intact while updating current availability."
        confirmLabel={destructiveLabel}
        onOpenChange={() => setPendingDelete(null)}
        onConfirm={() => pendingDelete && deleteMutation.mutate(pendingDelete)}
      />
    </div>
  );
}

function FormPanel({
  title,
  fields,
  initialValues,
  onCancel,
  onSubmit,
  isSaving,
}: {
  title: string;
  fields: FieldConfig[];
  initialValues: Record<string, unknown>;
  onCancel: () => void;
  onSubmit: (values: Record<string, unknown>) => void;
  isSaving: boolean;
}) {
  const [values, setValues] = useState<Record<string, unknown>>(initialValues);

  function setValue(name: string, value: unknown) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  return (
    <Card className="premium-panel border-[#d7e3e7]">
      <CardHeader>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">Details</p>
          <h3 className="mt-1 text-base font-semibold">{title}</h3>
        </div>
      </CardHeader>
      <CardContent>
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit(compactObject(values));
          }}
        >
          {fields.map((field) => (
            <div key={field.name} className={field.type === "textarea" ? "space-y-1.5 md:col-span-2" : "space-y-1.5"}>
              <Label>{field.label}</Label>
              {field.type === "textarea" ? (
                <Textarea value={String(values[field.name] ?? "")} required={field.required} onChange={(event) => setValue(field.name, event.target.value)} />
              ) : field.type === "select" ? (
                <Select value={String(values[field.name] ?? "")} required={field.required} onChange={(event) => setValue(field.name, event.target.value)}>
                  <option value="">Choose {field.label.toLowerCase()}</option>
                  {field.options?.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              ) : field.type === "checkbox" ? (
                <label className="flex h-10 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm">
                  <input
                    type="checkbox"
                    checked={Boolean(values[field.name])}
                    onChange={(event) => setValue(field.name, event.target.checked)}
                  />
                  Available
                </label>
              ) : (
                <Input
                  type={field.type ?? "text"}
                  value={String(values[field.name] ?? "")}
                  required={field.required}
                  onChange={(event) => setValue(field.name, event.target.value)}
                />
              )}
            </div>
          ))}
          <div className="flex justify-end gap-2 md:col-span-2">
            <Button type="button" variant="secondary" onClick={onCancel}>
              Cancel
            </Button>
            <Button disabled={isSaving}>{isSaving ? "Saving" : "Save changes"}</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export function dateColumn(value?: string | null) {
  return <span className="text-muted-foreground">{formatDate(value)}</span>;
}
