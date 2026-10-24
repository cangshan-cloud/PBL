export async function resolveCurrentComparison<T>(
  load: () => Promise<T>,
  isCurrent: () => boolean,
): Promise<T | null> {
  if (!isCurrent()) return null;
  const result = await load();
  return isCurrent() ? result : null;
}
