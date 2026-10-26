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

export async function loadForLatestRequest<T>(
  load: () => Promise<T>,
  session: number,
  currentSession: () => number,
  request: number,
  currentRequest: () => number,
): Promise<T | null> {
  try {
    const value = await loadForCurrentSession(load, session, currentSession);
    return currentRequest() === request ? value : null;
  } catch (error) {
    if (currentRequest() !== request) return null;
    throw error;
  }
}
