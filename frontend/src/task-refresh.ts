export type RefreshableTask = { status: string };

export const ACTIVE_TASK_REFRESH_MS = 2_000;
export const IDLE_TASK_REFRESH_MS = 30_000;

export function taskRefreshDelay(tasks: readonly RefreshableTask[] | null): number {
  return tasks?.some(task => task.status === "pending" || task.status === "running")
    ? ACTIVE_TASK_REFRESH_MS
    : IDLE_TASK_REFRESH_MS;
}
