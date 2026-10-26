import type { DailyCoverageRow } from "./daily-coverage";
import { csvCell } from "./csv-cell.ts";

const columns = ["run_id", "date", "candidate_symbols", "eligible_symbols", "coverage_ratio", "excluded_symbols", "ic_status", "group_status"];

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
