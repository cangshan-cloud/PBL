export type TaskFilterItem = { id: string; experiment_name?: string; status: string };
export type TaskStatusFilter = "all" | "success" | "running" | "pending" | "failed" | "cancelled";

export function filterTasks<T extends TaskFilterItem>(tasks: readonly T[], query: string, status: TaskStatusFilter): T[] {
  const needle = query.trim().toLocaleLowerCase();
  return tasks.filter(task =>
    (status === "all" || task.status === status) &&
    (!needle || task.id.toLocaleLowerCase().includes(needle) || (task.experiment_name ?? "").toLocaleLowerCase().includes(needle))
  );
}
