import { csvCell } from "./csv-cell.ts";

export type GroupNav = { group: number; points: { date: string; nav: number }[] };

export function groupNavCsv(runId: string, groups: readonly GroupNav[]): string {
  const lines = groups.flatMap(item => item.points.map(point =>
    [runId, item.group, point.date, point.nav].map(csvCell).join(","),
  ));
  return `\uFEFFrun_id,group,date,nav\r\n${lines.join("\r\n")}${lines.length ? "\r\n" : ""}`;
}

export function groupNavFilename(runId: string): string {
  return `group-nav-${runId.slice(0, 8)}.csv`;
}
