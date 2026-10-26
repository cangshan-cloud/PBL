export function reportListHint(reportCount: number, loading: boolean): string | null {
  if (reportCount > 0) return null;
  return loading ? "正在刷新研究报告…" : "成功完成研究后，报告会自动出现在这里。";
}

export type SearchableReport = { run_id: string; experiment_name: string };

export function filterReports<T extends SearchableReport>(reports: readonly T[], query: string): T[] {
  const needle = query.trim().toLocaleLowerCase();
  if (!needle) return [...reports];
  return reports.filter(report =>
    report.run_id.toLocaleLowerCase().includes(needle) || report.experiment_name.toLocaleLowerCase().includes(needle)
  );
}

export function selectVisibleReport<T extends SearchableReport>(reports: readonly T[], selectedRunId: string): T | undefined {
  return reports.find(report => report.run_id === selectedRunId) ?? reports[0];
}
