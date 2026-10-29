import { csvCell } from "./csv-cell.ts";
import type { ComponentIcRow } from "./ComponentIcTable.tsx";

export function componentIcCsv(runId: string, commonCoverage: number, rows: readonly ComponentIcRow[]): string {
  const lines = rows.map(row => [
    runId,
    row.factor,
    row.ic_mean,
    row.rank_ic_mean,
    row.valid_ic_dates,
    row.signal_date_count,
    commonCoverage,
  ].map(csvCell).join(","));
  return `\uFEFFrun_id,factor,ic_mean,rank_ic_mean,valid_ic_dates,signal_date_count,common_coverage\r\n${lines.join("\r\n")}${lines.length ? "\r\n" : ""}`;
}

export function componentIcFilename(runId: string): string {
  return `component-ic-${runId.slice(0, 8)}.csv`;
}

export function componentIcDailyCsv(runId: string, rows: readonly ComponentIcRow[]): string {
  const lines = rows.flatMap(row => (row.daily ?? []).map(day => [
    runId,
    row.factor,
    day.date,
    day.ic,
    day.rank_ic,
    day.observations,
  ].map(csvCell).join(",")));
  return `\uFEFFrun_id,factor,date,ic,rank_ic,observations\r\n${lines.join("\r\n")}${lines.length ? "\r\n" : ""}`;
}

export function componentIcDailyFilename(runId: string): string {
  return `component-ic-daily-${runId.slice(0, 8)}.csv`;
}
