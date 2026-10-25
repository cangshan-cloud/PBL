import type { DailyCoverageRow } from "./daily-coverage";

const columns = ["run_id", "date", "candidate_symbols", "eligible_symbols", "coverage_ratio", "excluded_symbols", "ic_status", "group_status"];

function csvCell(value: string | number | null | undefined): string {
  if (value == null) return "";
  const text = String(value);
  // Treat even unexpected server-provided strings as data when opened in a spreadsheet.
  const safe = /^[\s]*[=+\-@]/.test(text) ? `'${text}` : text;
  return /[",\r\n]/.test(safe) ? `"${safe.replaceAll('"', '""')}"` : safe;
}

export function dailyCoverageCsv(runId: string, rows: readonly DailyCoverageRow[]): string {
  const body = rows.map(row => [
    runId, row.date, row.candidate_symbols, row.eligible_symbols,
    row.coverage_ratio, row.excluded_symbols, row.ic_status, row.group_status,
  ].map(csvCell).join(","));
  return `\uFEFF${[columns.join(","), ...body].join("\r\n")}\r\n`;
}

export function dailyCoverageFilename(runId: string): string {
  return `daily-coverage-${runId.slice(0, 8)}.csv`;
}
