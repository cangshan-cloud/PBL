import { csvCell } from "./csv-cell.ts";

export type LongShortRow = {
  date: string;
  return: number;
  nav: number;
  turnover: number;
  cost: number;
  net_return: number;
  net_nav: number;
};

export function longShortCsv(runId: string, costBps: number, rows: readonly LongShortRow[]): string {
  const lines = rows.map(row => [
    runId, row.date, row.return, row.nav, row.turnover,
    row.cost, row.net_return, row.net_nav, costBps,
  ].map(csvCell).join(","));
  return `\uFEFFrun_id,date,gross_return,gross_nav,two_side_turnover,cost,net_return,net_nav,transaction_cost_bps\r\n${lines.join("\r\n")}${lines.length ? "\r\n" : ""}`;
}

export function longShortFilename(runId: string): string {
  return `long-short-${runId.slice(0, 8)}.csv`;
}
