export type ReportDownloadResponse = { ok: boolean; blob(): Promise<Blob> };

export async function downloadDisclosedReport(
  runId: string,
  fetchReport: (path: string) => Promise<ReportDownloadResponse>,
  save: (blob: Blob, filename: string) => void,
): Promise<string> {
  const response = await fetchReport(`/reports/${runId}/delivery`);
  if (!response.ok) throw new Error("披露版报告请求失败");
  const blob = await response.blob();
  if (!/^text\/html(?:;|$)/i.test(blob.type) || blob.size === 0) {
    throw new Error("披露版报告内容不是非空 HTML");
  }
  const filename = `factor-report-${runId.slice(0, 8)}-disclosed.html`;
  save(blob, filename);
  return filename;
}
