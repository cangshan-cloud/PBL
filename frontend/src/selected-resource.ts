export type SelectedResource<T> = { id: string; value: T };

export function forSelectedId<T>(resource: SelectedResource<T> | null, selectedId: string | undefined): T | null {
  return resource && resource.id === selectedId ? resource.value : null;
}
