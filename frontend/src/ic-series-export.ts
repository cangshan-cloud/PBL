import { csvCell } from "./csv-cell.ts";

export type IcSeriesRow = { date: string; ic: number | null; rank_ic: number | null };

export function icSeriesCsv(runId: string, rows: readonly IcSeriesRow[]): string {
  const lines = rows.map(row => [runId, row.date, row.ic, row.rank_ic].map(csvCell).join(","));
  return `\uFEFFrun_id,date,ic,rank_ic\r\n${lines.join("\r\n")}${lines.length ? "\r\n" : ""}`;
}

export function icSeriesFilename(runId: string): string {
  return `ic-series-${runId.slice(0, 8)}.csv`;
}
