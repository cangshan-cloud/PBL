export type RefreshableTask = { status: string };

export const ACTIVE_TASK_REFRESH_MS = 2_000;
export const IDLE_TASK_REFRESH_MS = 30_000;

export function taskRefreshDelay(tasks: readonly RefreshableTask[] | null): number {
  return tasks?.some(task => task.status === "pending" || task.status === "running")
    ? ACTIVE_TASK_REFRESH_MS
    : IDLE_TASK_REFRESH_MS;
}

export type TaskPollClock = {
  schedule(callback: () => void, delayMs: number): number;
  cancel(handle: number): void;
};

const browserClock: TaskPollClock = {
  schedule: (callback, delayMs) => window.setTimeout(callback, delayMs),
  cancel: handle => window.clearTimeout(handle),
};

export function startTaskPolling(
  load: () => Promise<readonly RefreshableTask[] | null>,
  onError: (error: unknown) => void,
  onSettled: () => void = () => undefined,
  clock: TaskPollClock = browserClock,
): () => void {
  let active = true;
  let timer: number | undefined;
  const refresh = async () => {
    let latest: readonly RefreshableTask[] | null = null;
    let failed = false;
    try { latest = await load(); }
    catch (error) { failed = true; if (active) onError(error); }
    if (!active) return;
    onSettled();
    timer = clock.schedule(() => { timer = undefined; void refresh(); }, failed ? IDLE_TASK_REFRESH_MS : taskRefreshDelay(latest));
  };
  void refresh();
  return () => { active = false; if (timer !== undefined) clock.cancel(timer); };
}
