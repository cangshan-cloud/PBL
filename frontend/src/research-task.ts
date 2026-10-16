export type PollableTask = { status: string };

export async function pollResearchTask<T extends PollableTask>(
  initial: T,
  load: () => Promise<T>,
  onUpdate: (task: T) => void,
  isCurrent: () => boolean,
  delay: () => Promise<void>,
): Promise<T | null> {
  let task = initial;
  while (task.status === "pending" || task.status === "running") {
    await delay();
    if (!isCurrent()) return null;
    const next = await load();
    if (!isCurrent()) return null;
    task = next;
    onUpdate(task);
  }
  return task;
}
