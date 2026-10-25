export function selectCoveragePage<T>(rows: T[], requestedPage: number, pageSize = 20) {
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError("page size must be positive");
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const page = Number.isInteger(requestedPage) ? Math.min(Math.max(requestedPage, 0), pageCount - 1) : 0;
  const start = page * pageSize;
  const end = Math.min(start + pageSize, rows.length);
  return { rows: rows.slice(start, end), page, pageCount, start, end, total: rows.length };
}
