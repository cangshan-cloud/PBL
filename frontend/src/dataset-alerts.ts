export type DatasetWithWeekendQuality = {
  id: string;
  name: string;
  dataset_key: string;
  version: string;
  checksum?: string;
  quality_report: { source?: string; dataset_kind?: string; columns?: string[]; weekend_date_count?: number; weekend_row_count?: number; announced_weekday_closure_date_count?: number; announced_weekday_closure_row_count?: number; announced_weekday_closure_dates?: string[]; announced_closure_calendar_version?: string; calendar_uncovered_years?: number[] };
};

export function weekendDatasetAlerts<T extends DatasetWithWeekendQuality>(datasets: T[]): T[] {
  return datasets.filter(item => (item.quality_report.weekend_row_count ?? 0) > 0);
}

export function selectedWeekendDatasetAlert<T extends DatasetWithWeekendQuality>(selected: T | undefined): T | undefined {
  return selected && (selected.quality_report.weekend_row_count ?? 0) > 0 ? selected : undefined;
}

export function calendarDatasetAlerts<T extends DatasetWithWeekendQuality>(datasets: T[]): T[] {
  return datasets.filter(item => (item.quality_report.announced_weekday_closure_row_count ?? 0) > 0 || (item.quality_report.calendar_uncovered_years?.length ?? 0) > 0);
}

export function isKnownSyntheticDemo(dataset: DatasetWithWeekendQuality | undefined): boolean {
  return dataset?.dataset_key === "demo_daily" && dataset.version === "0.2.0" &&
    dataset.checksum === "c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e";
}

export function importedCsvProvenanceNotice(dataset: DatasetWithWeekendQuality | undefined): string | null {
  if (!dataset || !Array.isArray(dataset.quality_report.columns) ||
      dataset.quality_report.dataset_kind === "hs300_bundle_v1" || isKnownSyntheticDemo(dataset) ||
      (dataset.dataset_key === "demo_daily" && dataset.quality_report.source === "bundled_demo")) return null;
  return "CSV 导入版本：格式与已知日期异常检查不认证数据真实性、使用授权或完整交易日历；请核对原始来源和交易所记录。";
}

export function reportDatasetByIdentity<T extends DatasetWithWeekendQuality>(
  datasets: T[], report: { dataset_version_id: string; dataset_checksum_sha256: string } | undefined,
): T | undefined {
  return report ? datasets.find(item => item.id === report.dataset_version_id && item.checksum === report.dataset_checksum_sha256) : undefined;
}

export function reportCalendarRiskNotice(dataset: DatasetWithWeekendQuality | undefined): string | null {
  if (!dataset) return null;
  const quality = dataset.quality_report;
  const count = quality.announced_weekday_closure_row_count ?? 0;
  const years = quality.calendar_uncovered_years ?? [];
  if (count <= 0 && years.length === 0) return null;
  const parts: string[] = [];
  if (count > 0) {
    parts.push(`${count} 行行情命中（${quality.announced_weekday_closure_dates?.join("、") || "日期见质量报告"}）`);
  }
  if (years.length) parts.push(`${years.join("、")} 年未覆盖`);
  parts.push(`规则版本：${quality.announced_closure_calendar_version ?? "未知"}`);
  return `当前报告的数据版本公告休市核对：${parts.join("；")}。仅供人工复核，旧归档 HTML 未改写。`;
}

export function adapterCalendarDetails(validation: {
  announced_closure_calendar_version?: string;
  announced_weekday_closure_dates?: string[];
  calendar_uncovered_years?: number[];
}): string | null {
  const dates = validation.announced_weekday_closure_dates ?? [];
  const years = validation.calendar_uncovered_years ?? [];
  if (!dates.length && !years.length) return null;
  const parts = [];
  if (dates.length) parts.push(`命中公告休市工作日：${dates.join("、")}`);
  if (years.length) parts.push(`未覆盖年份：${years.join("、")}`);
  parts.push(`规则版本：${validation.announced_closure_calendar_version ?? "未知"}`);
  return `${parts.join("；")}。仅供导入前人工复核，不自动删行。`;
}
