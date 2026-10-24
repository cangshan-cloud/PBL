export async function loadForCurrentSession<T>(
  load: () => Promise<T>,
  session: number,
  currentSession: () => number,
): Promise<T | null> {
  try {
    const value = await load();
    return currentSession() === session ? value : null;
  } catch (error) {
    if (currentSession() === session) throw error;
    return null;
  }
}
