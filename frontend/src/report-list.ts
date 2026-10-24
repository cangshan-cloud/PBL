export function reportListHint(reportCount: number, loading: boolean): string | null {
  if (reportCount > 0) return null;
  return loading ? "正在刷新研究报告…" : "成功完成研究后，报告会自动出现在这里。";
}
