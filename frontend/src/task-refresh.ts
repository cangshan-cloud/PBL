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

function startPolling<T>(
  load: () => Promise<T | null>,
  nextDelay: (value: T | null, failed: boolean) => number,
  onError: (error: unknown) => void,
  onSettled: () => void,
  clock: TaskPollClock,
): () => void {
  let active = true;
  let timer: number | undefined;
  const refresh = async () => {
    let latest: T | null = null;
    let failed = false;
    try { latest = await load(); }
    catch (error) { failed = true; if (active) onError(error); }
    if (!active) return;
    onSettled();
    timer = clock.schedule(() => { timer = undefined; void refresh(); }, nextDelay(latest, failed));
  };
  void refresh();
  return () => { active = false; if (timer !== undefined) clock.cancel(timer); };
}

export function startTaskPolling(
  load: () => Promise<readonly RefreshableTask[] | null>,
  onError: (error: unknown) => void,
  onSettled: () => void = () => undefined,
  clock: TaskPollClock = browserClock,
): () => void {
  return startPolling(load, (latest, failed) => failed ? IDLE_TASK_REFRESH_MS : taskRefreshDelay(latest), onError, onSettled, clock);
}

export function startReportPolling(
  load: () => Promise<unknown>,
  onError: (error: unknown) => void,
  onSettled: () => void = () => undefined,
  clock: TaskPollClock = browserClock,
): () => void {
  return startPolling(load, () => IDLE_TASK_REFRESH_MS, onError, onSettled, clock);
}
