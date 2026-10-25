export type DailyCoverageRow = {
  date: string;
  candidate_symbols?: number;
  eligible_symbols: number;
  excluded_symbols?: number;
  coverage_ratio?: number | null;
  ic_status: string;
  group_status: string;
};

export function needsCoverageReview(row: DailyCoverageRow): boolean {
  return (row.excluded_symbols ?? 0) > 0 || row.ic_status !== "valid" || row.group_status !== "valid";
}

export function selectCoverageRows(rows: DailyCoverageRow[], reviewOnly: boolean): DailyCoverageRow[] {
  return reviewOnly ? rows.filter(needsCoverageReview) : rows;
}

export function selectCoveragePage<T>(rows: T[], requestedPage: number, pageSize = 20) {
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError("page size must be positive");
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const page = Number.isInteger(requestedPage) ? Math.min(Math.max(requestedPage, 0), pageCount - 1) : 0;
  const start = page * pageSize;
  const end = Math.min(start + pageSize, rows.length);
  return { rows: rows.slice(start, end), page, pageCount, start, end, total: rows.length };
}
