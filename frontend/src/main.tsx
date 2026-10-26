import React from "react";
import { prepareAdapterImportBody } from "./adapter-upload";
import { adapterCalendarDetails, calendarDatasetAlerts, importedCsvProvenanceNotice, isKnownSyntheticDemo, reportCalendarRiskNotice, reportDatasetByIdentity, selectedWeekendDatasetAlert, weekendDatasetAlerts } from "./dataset-alerts";
import { downloadDisclosedReport } from "./report-download";
import { createRoot } from "react-dom/client";
import { buildResearchConfiguration, longShortGroupLabel, resultForConfiguration, validateResearchConfiguration } from "./research-config";
import { pollResearchTask } from "./research-task";
import { resolveCurrentComparison } from "./comparison-request";
import { loadForCurrentSession, loadForLatestRequest } from "./auth-resource";
import { comparisonDatasetLabel, comparisonDelta, comparisonSourceLabel } from "./comparison-format";
import { comparisonDownloadFilename, comparisonJsonContent } from "./comparison-download";
import { comparisonCandidateHint } from "./comparison-candidates";
import { filterReports, reportListHint, selectVisibleReport } from "./report-list";
import { saveBlobAsFile } from "./blob-download";
import { icSeriesCsv, icSeriesFilename } from "./ic-series-export";
import { longShortCsv, longShortFilename } from "./long-short-export";
import { groupNavCsv, groupNavFilename } from "./group-nav-export";
import { alignNavLines, type NavLine } from "./chart-series";
import { DailyCoverageTable } from "./DailyCoverageTable";
import { filterTasks, type TaskStatusFilter } from "./task-filter";
import { startReportPolling, startTaskPolling } from "./task-refresh";
import { forSelectedId, type SelectedResource } from "./selected-resource";
import "./styles.css";
import "./layout.css";

type CompositeResult = { method: string; weights: Record<string, number>; component_coverage: Record<string, number>; common_coverage: number; correlation_matrix: { left: string; right: string; correlation: number | null }[] };
type HistoricalAudit = Record<string, { totals: Record<string, number>; daily: { date: string; [key: string]: string | number }[]; unlabeled_signals: { date: string; symbol: string; factor: number; next_market_date: string | null; reason: string }[] }>;
type Result = { coverage: number; candidate_coverage?: number; coverage_ratio?: number | null; zero_observation_days?: number; daily_coverage?: { date: string; candidate_symbols?: number; eligible_symbols: number; excluded_symbols?: number; coverage_ratio?: number | null; ic_status: string; group_status: string }[]; time_split?: { validation_start_date: string; embargo_signal_date: string; research: { start_date: string; end_date: string; observation_count: number; signal_date_count: number; valid_ic_dates: number; ic_mean: number | null; rank_ic_mean: number | null; icir: number | null; ic_positive_ratio: number | null }; validation: { start_date: string; end_date: string; observation_count: number; signal_date_count: number; valid_ic_dates: number; ic_mean: number | null; rank_ic_mean: number | null; icir: number | null; ic_positive_ratio: number | null } }; ic_mean: number | null; ic_std: number | null; rank_ic_mean: number | null; icir: number | null; ic_positive_ratio: number | null; long_short_mean: number | null; long_short_total_return: number | null; long_short_net_total_return: number | null; long_short_turnover: number | null; transaction_cost_bps: number; top_group_turnover: number | null; group_skipped_constant_factor_days?: number; group_skipped_insufficient_sample_days?: number; ic_series: { date: string; ic: number | null; rank_ic: number | null }[]; ic_histogram?: { lower: number; upper: number; count: number }[]; group_nav: { group: number; points: { date: string; nav: number }[] }[]; long_short_series: { date: string; return: number; nav: number; turnover: number; cost: number; net_return: number; net_nav: number }[]; group_returns: { group: number; mean_return: number }[]; composite?: CompositeResult; historical_audit?: HistoricalAudit };
type Task = { id: string; experiment_id?: string; experiment_name?: string; status: string; progress?: number; result?: Result; error_summary?: string; queued_at?: string; started_at?: string | null; finished_at?: string | null; cancellation_requested_at?: string | null; parameters?: Record<string, unknown>; dataset_version_id?: string; dataset_version?: string; factor_version_id?: string; factor_version?: string; code_version?: string };
type RunLog = { id: string; level: string; event: string; message: string; created_at: string };
type QualityReport = { valid?: boolean; dataset_kind?: string; bundle_id?: string; verified_files?: number; member_trading_days?: number; columns?: string[]; missing_counts?: Record<string, number>; missing_adj_factor_by_symbol?: Record<string, number>; completeness?: Record<string, number>; numeric_summary?: Record<string, { count: number; min: number; max: number; mean: number }>; inferred_market_date_count?: number; weekend_date_count?: number; weekend_row_count?: number; announced_closure_calendar_version?: string; announced_weekday_closure_date_count?: number; announced_weekday_closure_row_count?: number; announced_weekday_closure_dates?: string[]; calendar_uncovered_years?: number[]; internal_calendar_gap_count?: number; symbols_with_internal_calendar_gaps?: number; adapter_report?: { source_adjustment_flags?: unknown } };
type Dataset = { id: string; dataset_key: string; name: string; version: string; start_date: string | null; end_date: string | null; row_count: number; symbol_count: number; checksum: string; source_filename: string; status: string; quality_report: QualityReport };
type DatasetPreview = { dataset_id: string; columns: string[]; rows: Record<string, string>[]; preview_count: number; total_rows: number; truncated: boolean };
type AdapterPreview = { source_sha256: string; report: { source_encoding: string; column_mapping: Record<string, string>; dropped_columns: string[]; converted_rows: number; warnings: string[]; validation: { row_count: number; symbol_count: number; start_date: string; end_date: string; announced_closure_calendar_version?: string; announced_weekday_closure_dates?: string[]; calendar_uncovered_years?: number[] } }; preview: Record<string, string>[] };
type Report = { run_id: string; experiment_name: string; dataset_version: string; dataset_version_id: string; dataset_checksum_sha256: string; factor_version: string; created_at: string; checksum: string };
type User = { id: string; username: string; display_name: string; role: "admin" | "researcher" | "viewer"; is_active: boolean; created_at: string };
type Factor = { id: string; name: string; category: string; version: string; formula: string; description: string; required_columns: string[]; default_lookback: number | null; status: string };
type Dashboard = { scope: "personal" | "global"; datasets: { total: number; published: number; draft: number; latest_name: string | null }; factors: { builtin: number; composite_available: boolean }; tasks: { total: number; by_status: Record<string, number>; success_rate: number | null }; reports: { total: number }; recent_tasks: Task[]; recent_reports: Report[] };
type ComparisonItem = { run_id: string; experiment_name: string; factor: string; dataset_version_id: string; dataset_checksum_sha256: string; dataset_source_kind: "bundled_demo" | "historical_bundle" | "imported_csv"; dataset_version: string; price_basis: "source_close" | "factor_adjusted"; groups: number; metrics: Record<string, number | null>; common_date_ic: { ic_mean: number | null; rank_ic_mean: number | null; icir: number | null; ic_positive_ratio: number | null; rank_ic_valid_dates: number }; validation_start_date: string | null; validation_ic: { valid_ic_dates: number | null; ic_mean: number | null; rank_ic_mean: number | null; icir: number | null; ic_positive_ratio: number | null } | null; observation_artifact_count: number | null; validation_artifact_count: number | null; delta_from_baseline: Record<string, number | null>; ic_date_count: number; group_date_count: number; ic_start_date: string | null; ic_end_date: string | null; sample_symbols: string[]; preprocessing: { winsorize: boolean; standardize: boolean; mad_scale: number | null }; code_version: string };
type MatchedComparison = { available: boolean; reason?: string; validation_start_date?: string; observation_count?: number; date_count?: number; label_mismatch_count?: number; min_valid_ic_dates?: number; min_retention_ratio?: number | null; evidence?: { level: "insufficient" | "limited" | "descriptive"; note: string }; items?: { run_id: string; ic_mean: number | null; rank_ic_mean: number | null; icir: number | null; ic_positive_ratio: number | null; valid_ic_dates: number; source_observation_count: number | null; retention_ratio: number | null }[] };
type Comparison = { baseline_run_id: string; items: ComparisonItem[]; rankings: Record<string, string[]>; common_ic_date_count: number; common_group_date_count: number; common_validation_ic_date_count: number | null; matched_sample: MatchedComparison; matched_validation_sample: MatchedComparison; comparable: boolean; warnings: string[] };
type Conclusion = { run_id: string; grade: string; headline: string; evidence: string[]; limitations: string[]; next_steps: string[]; method: { type: string; version: string }; disclaimer: string };
const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
let currentToken = window.localStorage.getItem("factorlab_token") ?? "";

function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (currentToken) headers.set("Authorization", `Bearer ${currentToken}`);
  return fetch(`${apiBase}${path}`, { ...init, headers });
}

function number(value: number | null | undefined, percent = false) {
  if (value == null) return "—";
  return percent ? `${(value * 100).toFixed(2)}%` : value.toFixed(4);
}

function errorMessage(payload: unknown, fallback: string) {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) return fallback;
  const detail = (payload as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (typeof detail === "object" && detail !== null && "message" in detail) return String(detail.message);
  return fallback;
}

function formatTime(value?: string | null) {
  if (!value) return "—";
  const instant = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`;
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "short", timeStyle: "medium" }).format(new Date(instant));
}

function statusLabel(status: string) {
  return ({ pending: "等待执行", running: "运行中", success: "成功", failed: "失败", cancelled: "已取消" } as Record<string, string>)[status] ?? status;
}

const groupColors = ["#277a5b", "#65a563", "#a5a944", "#d5a04b", "#b86e52", "#6d8bc3", "#805ca8", "#bc73aa", "#4e9ca3", "#707b7b"];

function NavChart({ eyebrow, title, lines, knownDates = [], note, action, wide = false }: { eyebrow: string; title: string; lines: NavLine[]; knownDates?: string[]; note: string; action?: React.ReactNode; wide?: boolean }) {
  const aligned = alignNavLines(lines, knownDates);
  const valid = aligned.lines.flatMap(line => line.segments.flatMap(segment => segment.map(point => point.value)));
  let low = Math.min(1, ...valid); let high = Math.max(1, ...valid);
  if (low === high) { low -= 0.05; high += 0.05; }
  const padding = (high - low) * 0.08;
  low -= padding; high += padding;
  const y = (value: number) => 180 - (value - low) * 180 / (high - low);
  const x = (index: number) => aligned.dates.length === 1 ? 300 : index * 600 / (aligned.dates.length - 1);
  return <article className={`card line-chart${wide ? " group-nav" : ""}`}><p className="eyebrow">{eyebrow}</p><div className="section-title"><h2>{title}</h2>{action}</div>
    {valid.length ? <svg viewBox="0 0 600 180" preserveAspectRatio="none" role="img" aria-label={`${title}，按结果日期等距排列`}>
      <line x1="0" y1={y(1)} x2="600" y2={y(1)} />
      {aligned.lines.flatMap(line => line.segments.map((segment, index) => segment.length > 1
        ? <polyline key={`${line.label}-${index}`} style={{ stroke: line.color }} points={segment.map(point => `${x(point.index)},${y(point.value)}`).join(" ")} />
        : <circle key={`${line.label}-${index}`} cx={x(segment[0].index)} cy={y(segment[0].value)} r="3" style={{ fill: line.color }} />))}
    </svg> : <div className="empty">暂无净值序列。</div>}
    {aligned.dates.length > 0 && <div className="chart-date-range"><span>{aligned.dates[0]}</span><span>{aligned.dates.at(-1)}</span></div>}
    <div className="chart-legend">{aligned.lines.map(line => <span key={line.label}><i style={{ background: line.color }} />{line.label} · {number(line.lastValue)}</span>)}</div>
    <small>{note}；横向按已知结果/诊断日期等距，非自然日间隔；已知缺日断线。</small>
  </article>;
}

function icHistogram(values: (number | null)[]) {
  const counts = Array(10).fill(0) as number[];
  values.forEach(value => {
    if (value != null && Number.isFinite(value)) counts[Math.min(9, Math.max(0, Math.floor((value + 1) * 5 + 1e-12)))] += 1;
  });
  return counts.map((count, index) => ({ lower: Number((-1 + index * 0.2).toFixed(1)), upper: Number((-0.8 + index * 0.2).toFixed(1)), count }));
}

function IcSeriesChart({ runId, series, knownDates = [], showDownload = true }: { runId: string; series: Result["ic_series"]; knownDates?: string[]; showDownload?: boolean }) {
  const values = series.map(item => item.ic);
  const valid = values.filter((value): value is number => value != null && Number.isFinite(value));
  const low = Math.min(0, ...valid); const high = Math.max(0, ...valid);
  const span = high - low || 1; const padding = span * 0.08;
  const y = (value: number) => 180 - (value - (low - padding)) * 180 / (span + padding * 2);
  const aligned = alignNavLines([{
    label: "IC", color: "#3f765d", points: series.map(item => ({ date: item.date, value: item.ic ?? Number.NaN })),
  }], [...knownDates, ...series.map(item => item.date)]);
  const segments = aligned.lines[0].segments;
  const x = (index: number) => aligned.dates.length === 1 ? 300 : index * 600 / (aligned.dates.length - 1);
  return <article className="card line-chart"><p className="eyebrow">IC SERIES</p><div className="section-title"><h2>每日 IC</h2>{showDownload && <button className="secondary" onClick={() => saveBlobAsFile(new Blob([icSeriesCsv(runId, series)], { type: "text/csv;charset=utf-8" }), icSeriesFilename(runId))}>下载每日 IC CSV</button>}</div>{valid.length ? <svg viewBox="0 0 600 180" preserveAspectRatio="none" role="img" aria-label="每日 IC，已知缺日处断开"><line x1="0" y1={y(0)} x2="600" y2={y(0)} />{segments.map((segment, index) => segment.length > 1 ? <polyline key={index} points={segment.map(point => `${x(point.index)},${y(point.value)}`).join(" ")} /> : <circle key={index} cx={x(segment[0].index)} cy={y(segment[0].value)} r="3" />)}</svg> : <div className="empty">没有可计算的 IC。</div>}{aligned.dates.length > 0 && <div className="chart-date-range"><span>{aligned.dates[0]}</span><span>{aligned.dates.at(-1)}</span></div>}<small>{valid.length} 个有效截面；{aligned.dates.length - series.length} 个已知日期无 IC 记录、{values.length - valid.length} 个原记录为空值，均不填零。横向按已知结果/诊断日期等距，非自然日间隔；CSV 保留原序列日期与数值。</small></article>;
}

function IcDistribution({ result }: { result: Result }) {
  const histogram = result.ic_histogram ?? icHistogram(result.ic_series.map(item => item.ic));
  const maximum = Math.max(1, ...histogram.map(item => item.count));
  const total = histogram.reduce((sum, item) => sum + item.count, 0);
  return <article className="card ic-distribution"><p className="eyebrow">IC DISTRIBUTION</p><h2>IC 分布</h2><div className="bars">{histogram.map(item => <div className="bar-row" key={item.lower}><span>{item.lower.toFixed(1)}～{item.upper.toFixed(1)}</span><div><i style={{ width: `${item.count / maximum * 100}%` }} /></div><strong>{item.count}</strong></div>)}</div><small>固定 0.2 宽度分箱 · {total} 个有效交易日，空值不计入</small></article>;
}

function SavedSeriesCharts({ runId, result, onDownloadLongShort, onDownloadGroupNav, showActions = true, includeDistribution = true }: {
  runId: string;
  result: Result;
  onDownloadLongShort: (runId: string, result: Result) => void;
  onDownloadGroupNav: (runId: string, result: Result) => void;
  showActions?: boolean;
  includeDistribution?: boolean;
}) {
  const knownDates = result.daily_coverage?.map(item => item.date) ?? [];
  return <section className="chart-grid" aria-label={`Run ${runId} 的逐日曲线`}>
    <IcSeriesChart runId={runId} series={result.ic_series} knownDates={knownDates} showDownload={showActions} />
    <NavChart eyebrow="LONG SHORT NAV" title="多空组合净值" lines={[
      { label: "毛净值", color: "#277a5b", points: result.long_short_series.map(item => ({ date: item.date, value: item.nav })) },
      { label: "成本后净值", color: "#d69043", points: result.long_short_series.map(item => ({ date: item.date, value: item.net_nav })) },
    ]} knownDates={knownDates} note={`初值 1；成本后净值扣除 ${result.transaction_cost_bps} bps 单边成本`}
      action={showActions && <button className="secondary" onClick={() => onDownloadLongShort(runId, result)}>下载多空逐日 CSV</button>} />
    {includeDistribution && <IcDistribution result={result} />}
    <NavChart eyebrow="QUANTILE NAV" title="各组净值" lines={(result.group_nav ?? []).map(item => ({
      label: `Q${item.group}`, color: groupColors[(item.group - 1) % groupColors.length],
      points: item.points.map(point => ({ date: point.date, value: point.nav })),
    }))} knownDates={knownDates} note="各组等权日收益连乘，初值 1；与分组平均收益使用同一结果数据"
      action={showActions && <button className="secondary" onClick={() => onDownloadGroupNav(runId, result)}>下载各组逐日净值 CSV</button>} wide />
  </section>;
}

function App() {
  const [user, setUser] = React.useState<User | null>(null);
  const [authChecked, setAuthChecked] = React.useState(false);
  const [view, setView] = React.useState<"dashboard" | "research" | "factors" | "datasets" | "tasks" | "comparisons" | "reports" | "users">("dashboard");
  const [dashboard, setDashboard] = React.useState<Dashboard | null>(null);
  const [users, setUsers] = React.useState<User[]>([]);
  const [rawTask, setTask] = React.useState<Task | null>(null);
  const [taskConfigKey, setTaskConfigKey] = React.useState("");
  const [tasks, setTasks] = React.useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = React.useState("");
  const [taskQuery, setTaskQuery] = React.useState("");
  const [taskStatusFilter, setTaskStatusFilter] = React.useState<TaskStatusFilter>("all");
  const [taskLogs, setTaskLogs] = React.useState<SelectedResource<RunLog[]> | null>(null);
  const [taskConclusion, setTaskConclusion] = React.useState<Conclusion | null>(null);
  const [comparisonRunIds, setComparisonRunIds] = React.useState<string[]>([]);
  const [comparison, setComparison] = React.useState<Comparison | null>(null);
  const [comparisonCandidatesLoading, setComparisonCandidatesLoading] = React.useState(false);
  const [reports, setReports] = React.useState<Report[]>([]);
  const [reportListLoading, setReportListLoading] = React.useState(false);
  const [reportQuery, setReportQuery] = React.useState("");
  const [selectedReportId, setSelectedReportId] = React.useState("");
  const [reportHtml, setReportHtml] = React.useState<SelectedResource<string> | null>(null);
  const [datasets, setDatasets] = React.useState<Dataset[]>([]);
  const [factors, setFactors] = React.useState<Factor[]>([]);
  const [selectedFactorKey, setSelectedFactorKey] = React.useState("momentum_20d");
  const [researchMode, setResearchMode] = React.useState<"single" | "composite" | "historical">("single");
  const [priceBasis, setPriceBasis] = React.useState<"source_close" | "factor_adjusted">("source_close");
  const [compositeFactors, setCompositeFactors] = React.useState(["momentum_20d", "reversal_5d"]);
  const [lookback, setLookback] = React.useState(20);
  const [winsorize, setWinsorize] = React.useState(true);
  const [standardize, setStandardize] = React.useState(true);
  const [groups, setGroups] = React.useState(5);
  const [transactionCostBps, setTransactionCostBps] = React.useState(10);
  const [selectedDataset, setSelectedDataset] = React.useState("");
  const [bundleId, setBundleId] = React.useState("");
  const [sampleStart, setSampleStart] = React.useState("");
  const [sampleEnd, setSampleEnd] = React.useState("");
  const [validationStart, setValidationStart] = React.useState("");
  const [sampleSymbols, setSampleSymbols] = React.useState("");
  const [datasetPreview, setDatasetPreview] = React.useState<DatasetPreview | null>(null);
  const [adapterPreview, setAdapterPreview] = React.useState<AdapterPreview | null>(null);
  const [adapterPreviewAttempted, setAdapterPreviewAttempted] = React.useState(false);
  const [adapterPreviewInvalidated, setAdapterPreviewInvalidated] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [comparisonLoading, setComparisonLoading] = React.useState(false);
  const researchSession = React.useRef(0);
  const comparisonSession = React.useRef(0);
  const authSession = React.useRef(0);
  const taskLoadSerial = React.useRef(0);
  const reportLoadSerial = React.useRef(0);
  const latestTaskSnapshot = React.useRef<Task[]>([]);
  const [notice, setNotice] = React.useState("");
  const published = datasets.filter(item => item.status === "published");
  const isHistoricalDataset = (item: Dataset) => item.quality_report.dataset_kind === "hs300_bundle_v1";
  const eligibleDatasets = published.filter(item => researchMode === "historical" ? isHistoricalDataset(item) : !isHistoricalDataset(item));
  const selected = eligibleDatasets.find(item => item.id === selectedDataset) ?? eligibleDatasets[0];
  const selectedFactor = factors.find(item => item.id === selectedFactorKey) ?? factors[0];
  const visibleTasks = filterTasks(tasks, taskQuery, taskStatusFilter);
  const selectedTask = visibleTasks.find(item => item.id === selectedTaskId) ?? visibleTasks[0];
  const visibleReports = filterReports(reports, reportQuery);
  const selectedReport = selectVisibleReport(visibleReports, selectedReportId);
  const selectedReportDataset = reportDatasetByIdentity(datasets, selectedReport);
  const reportCalendarNotice = reportCalendarRiskNotice(selectedReportDataset);
  const calendarPreviewDetails = adapterPreview ? adapterCalendarDetails(adapterPreview.report.validation) : null;
  const visibleTaskLogs = forSelectedId(taskLogs, selectedTask?.id);
  const visibleTaskConclusion = taskConclusion?.run_id === selectedTask?.id ? taskConclusion : null;
  const visibleReportHtml = forSelectedId(reportHtml, selectedReport?.run_id);

  const openSelectedReportTask = () => {
    if (!selectedReport) return;
    setSelectedTaskId(selectedReport.run_id);
    setTaskQuery(selectedReport.run_id);
    setTaskStatusFilter("all");
    setView("tasks");
  };
  const openSelectedTaskReport = () => {
    if (!selectedTask || selectedTask.status !== "success") return;
    setSelectedReportId(selectedTask.id);
    setReportQuery(selectedTask.id);
    setReportListLoading(true);
    setView("reports");
  };
  const downloadLongShort = (runId: string, result: Result) => {
    saveBlobAsFile(
      new Blob([longShortCsv(runId, result.transaction_cost_bps, result.long_short_series)], { type: "text/csv;charset=utf-8" }),
      longShortFilename(runId),
    );
  };
  const downloadGroupNav = (runId: string, result: Result) => {
    saveBlobAsFile(
      new Blob([groupNavCsv(runId, result.group_nav ?? [])], { type: "text/csv;charset=utf-8" }),
      groupNavFilename(runId),
    );
  };
  const researchInput = {
    mode: researchMode,
    datasetId: selected?.id ?? null,
    factorId: selectedFactor?.id ?? null,
    factorDefaultLookback: selectedFactor?.default_lookback ?? null,
    compositeFactors,
    lookback,
    groups,
    winsorize,
    standardize,
    transactionCostBps,
    priceBasis,
    sourceAdjustmentFlags: selected?.quality_report.adapter_report?.source_adjustment_flags,
    datasetColumns: selected?.quality_report.columns,
    missingAdjustmentCount: selected?.quality_report.missing_counts?.adj_factor,
    missingAdjustmentBySymbol: selected?.quality_report.missing_adj_factor_by_symbol,
    sampleStart,
    sampleEnd,
    validationStart,
    sampleSymbols,
  };
  const { parameters: researchParameters, key: researchConfigKey } = buildResearchConfiguration(researchInput);
  const researchValidationError = validateResearchConfiguration(researchInput, selected?.start_date, selected?.end_date);
  const task = resultForConfiguration(rawTask, taskConfigKey, researchConfigKey);

  const loadDatasets = React.useCallback(async () => {
    const session = authSession.current;
    const value = await loadForCurrentSession(async () => {
      const response = await apiFetch("/datasets");
      if (!response.ok) throw new Error("数据版本加载失败");
      return response.json() as Promise<Dataset[]>;
    }, session, () => authSession.current);
    if (!value) return;
    setDatasets(value);
    setSelectedDataset(current => current || value.find(item => item.status === "published")?.id || "");
  }, []);

  const loadFactors = React.useCallback(async () => {
    const session = authSession.current;
    const value = await loadForCurrentSession(async () => {
      const response = await apiFetch("/factors");
      if (!response.ok) throw new Error("因子库加载失败");
      return response.json() as Promise<Factor[]>;
    }, session, () => authSession.current);
    if (value) setFactors(value);
  }, []);

  const loadDashboard = React.useCallback(async () => {
    const session = authSession.current;
    const value = await loadForCurrentSession(async () => {
      const response = await apiFetch("/dashboard");
      if (!response.ok) throw new Error("项目总览加载失败");
      return response.json() as Promise<Dashboard>;
    }, session, () => authSession.current);
    if (value) setDashboard(value);
  }, []);

  const loadUsers = React.useCallback(async () => {
    const session = authSession.current;
    const value = await loadForCurrentSession(async () => {
      const response = await apiFetch("/users");
      if (!response.ok) throw new Error("用户列表加载失败");
      return response.json() as Promise<User[]>;
    }, session, () => authSession.current);
    if (value) setUsers(value);
  }, []);

  const loadTasks = React.useCallback(async () => {
    const session = authSession.current;
    const request = ++taskLoadSerial.current;
    const value = await loadForLatestRequest(async () => {
      const response = await apiFetch("/research/tasks");
      if (!response.ok) throw new Error("任务列表加载失败");
      return response.json() as Promise<Task[]>;
    }, session, () => authSession.current, request, () => taskLoadSerial.current);
    if (!value) return null;
    latestTaskSnapshot.current = value;
    setTasks(value);
    setSelectedTaskId(current => value.some(item => item.id === current) ? current : value[0]?.id || "");
    return value;
  }, []);

  const loadReports = React.useCallback(async () => {
    const session = authSession.current;
    const request = ++reportLoadSerial.current;
    const value = await loadForLatestRequest(async () => {
      const response = await apiFetch("/reports");
      if (!response.ok) throw new Error("报告列表加载失败");
      return response.json() as Promise<Report[]>;
    }, session, () => authSession.current, request, () => reportLoadSerial.current);
    if (!value) return null;
    setReports(value);
    setSelectedReportId(current => value.some(item => item.run_id === current) ? current : value[0]?.run_id || "");
    return value;
  }, []);

  React.useEffect(() => {
    if (!currentToken) { setAuthChecked(true); return; }
    apiFetch("/auth/me").then(async response => {
      if (!response.ok) throw new Error("登录已过期");
      setUser(await response.json() as User);
    }).catch(() => { currentToken = ""; window.localStorage.removeItem("factorlab_token"); }).finally(() => setAuthChecked(true));
  }, []);
  React.useEffect(() => {
    if (!user) return;
    Promise.all([loadDatasets(), loadFactors(), loadDashboard()]).catch(error => setNotice(String(error)));
  }, [user, loadDatasets, loadFactors, loadDashboard]);
  React.useEffect(() => {
    if (!selected) return;
    setSampleStart(selected.start_date ?? "");
    setSampleEnd(selected.end_date ?? "");
  }, [selected?.id]);
  React.useEffect(() => {
    if (!user || view !== "tasks") return;
    return startTaskPolling(
      async () => (await loadTasks()) ?? latestTaskSnapshot.current,
      error => setNotice(String(error)),
    );
  }, [user, view, loadTasks]);
  React.useEffect(() => {
    if (!user || view !== "comparisons") return;
    setComparisonCandidatesLoading(true);
    return startTaskPolling(
      async () => (await loadTasks()) ?? latestTaskSnapshot.current,
      error => setNotice(String(error)),
      () => setComparisonCandidatesLoading(false),
    );
  }, [user, view, loadTasks]);
  React.useEffect(() => {
    if (!user || view !== "reports") return;
    setReportListLoading(true);
    return startReportPolling(
      loadReports,
      error => setNotice(String(error)),
      () => setReportListLoading(false),
    );
  }, [user, view, loadReports]);
  React.useEffect(() => { if (user?.role === "admin" && view === "users") loadUsers().catch(error => setNotice(String(error))); }, [user, view, loadUsers]);
  React.useEffect(() => {
    if (!user || view !== "reports" || !selectedReport) { setReportHtml(null); return; }
    let active = true;
    apiFetch(`/reports/${selectedReport.run_id}/html`).then(async response => {
      if (!response.ok) throw new Error("报告预览加载失败");
      const html = await response.text();
      if (active) setReportHtml({ id: selectedReport.run_id, value: html });
    }).catch(error => { if (active) setNotice(String(error)); });
    return () => { active = false; };
  }, [user, view, selectedReport?.run_id]);
  React.useEffect(() => {
    if (!user || view !== "tasks" || !selectedTask) { setTaskLogs(null); return; }
    let active = true;
    apiFetch(`/research/tasks/${selectedTask.id}/logs`).then(async response => {
      if (!response.ok) throw new Error("任务日志加载失败");
      const logs = await response.json() as RunLog[];
      if (active) setTaskLogs({ id: selectedTask.id, value: logs });
    }).catch(error => { if (active) setNotice(String(error)); });
    return () => { active = false; };
  }, [user, view, selectedTask?.id, selectedTask?.status]);
  React.useEffect(() => {
    if (!user || view !== "tasks" || selectedTask?.status !== "success") { setTaskConclusion(null); return; }
    let active = true;
    apiFetch(`/research/tasks/${selectedTask.id}/conclusion`).then(async response => {
      if (!response.ok) throw new Error("研究结论加载失败");
      const conclusion = await response.json() as Conclusion;
      if (active) setTaskConclusion(conclusion);
    }).catch(error => { if (active) setNotice(String(error)); });
    return () => { active = false; };
  }, [user, view, selectedTask?.id, selectedTask?.status]);

  async function runResearch() {
    if (!researchParameters) { setNotice(researchMode === "historical" ? "请先注册并发布历史沪深300数据包" : "请先选择可用的数据版本与研究因子"); setView("datasets"); return; }
    if (researchValidationError) { setNotice(researchValidationError); return; }
    const session = ++researchSession.current;
    const isCurrent = () => researchSession.current === session;
    setLoading(true); setNotice(""); setTask(null); setTaskConfigKey(researchConfigKey);
    try {
      const endpoint = researchMode === "historical" ? "/research/historical-tasks" : researchMode === "composite" ? "/research/composite-tasks" : "/research/tasks";
      const response = await apiFetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(researchParameters) });
      const payload = await response.json();
      if (!isCurrent()) return;
      const value = payload as Task;
      if (!response.ok) throw new Error(errorMessage(payload, "任务提交失败"));
      setTask(value);
      await pollResearchTask(value, async () => {
        const poll = await apiFetch(`/research/tasks/${value.id}`);
        const pollPayload = await poll.json();
        if (!poll.ok) throw new Error(errorMessage(pollPayload, "任务状态查询失败"));
        return pollPayload as Task;
      }, setTask, isCurrent, () => new Promise(resolve => window.setTimeout(resolve, 500)));
    } catch (error) { if (isCurrent()) setTask({ id: "local-error", status: "failed", error_summary: String(error) }); }
    finally { if (isCurrent()) { setLoading(false); loadTasks().catch(() => undefined); loadReports().catch(() => undefined); loadDashboard().catch(() => undefined); } }
  }

  async function uploadDataset(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setNotice("");
    const form = event.currentTarget;
    try {
      const body = prepareAdapterImportBody(new FormData(form), adapterPreview, adapterPreviewInvalidated);
      const response = await apiFetch("/datasets/import", { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "数据导入失败"));
      setNotice(`已导入 ${payload.name}，请检查后发布`); form.reset(); setAdapterPreview(null);
      setAdapterPreviewAttempted(false); setAdapterPreviewInvalidated(false); await loadDatasets();
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  async function registerHistoricalBundle(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setNotice("");
    try {
      const response = await apiFetch("/datasets/register-hs300-bundle", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bundle_id: bundleId.trim() }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "历史包注册失败"));
      setBundleId(""); setNotice(`历史数据包 ${payload.version} 已注册为草稿，请核对后发布`);
      await loadDatasets();
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  async function previewAdapter(event: React.MouseEvent<HTMLButtonElement>) {
    const form = event.currentTarget.form;
    const file = form?.elements.namedItem("file") as HTMLInputElement | null;
    if (!file?.files?.[0]) { setNotice("请先选择需要适配的 CSV 文件"); return; }
    const selectedFile = file.files[0];
    const body = new FormData(); body.append("file", selectedFile);
    setAdapterPreviewAttempted(true); setLoading(true); setNotice("");
    try {
      const response = await apiFetch("/datasets/adapt/preview", { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "字段适配预览失败"));
      if (file.files?.[0] !== selectedFile) return;
      setAdapterPreview(payload as AdapterPreview);
      setAdapterPreviewInvalidated(false);
      const normalize = form?.elements.namedItem("normalize_cn_csv") as HTMLInputElement | null;
      if (normalize) normalize.checked = true;
    } catch (error) { setNotice(String(error)); setAdapterPreview(null); }
    finally { setLoading(false); }
  }

  async function publishDataset(id: string) {
    setLoading(true); setNotice("");
    try {
      const response = await apiFetch(`/datasets/${id}/publish`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "发布失败"));
      setNotice(`数据版本 ${payload.version} 已发布`); await loadDatasets(); setSelectedDataset(id);
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  async function toggleDatasetPreview(id: string) {
    if (datasetPreview?.dataset_id === id) { setDatasetPreview(null); return; }
    setLoading(true); setNotice("");
    try {
      const response = await apiFetch(`/datasets/${id}/preview?limit=20`);
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "数据预览加载失败"));
      setDatasetPreview(payload as DatasetPreview);
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  async function login(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setNotice("");
    const data = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${apiBase}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: data.get("username"), password: data.get("password") }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "登录失败"));
      currentToken = payload.access_token; window.localStorage.setItem("factorlab_token", currentToken);
      const me = await apiFetch("/auth/me");
      setUser(await me.json() as User);
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  function logout() {
    researchSession.current += 1;
    comparisonSession.current += 1;
    authSession.current += 1;
    currentToken = "";
    window.localStorage.removeItem("factorlab_token");
    setUser(null);
    setView("dashboard");
    setDashboard(null);
    setUsers([]);
    setDatasets([]);
    setFactors([]);
    setTask(null);
    setTaskConfigKey("");
    setTasks([]);
    latestTaskSnapshot.current = [];
    setSelectedTaskId("");
    setTaskLogs(null);
    setTaskConclusion(null);
    setComparisonRunIds([]);
    setComparison(null);
    setComparisonLoading(false);
    setReports([]);
    setSelectedReportId("");
    setReportHtml(null);
    setDatasetPreview(null);
    setAdapterPreview(null);
    setAdapterPreviewAttempted(false);
    setAdapterPreviewInvalidated(false);
    setNotice("");
    setLoading(false);
  }

  async function downloadReport() {
    if (!selectedReport) return;
    setNotice("");
    try {
      const filename = await downloadDisclosedReport(selectedReport.run_id, apiFetch, saveBlobAsFile);
      setNotice(`已发起 ${filename} 下载；请在浏览器下载列表确认文件。原始归档未改写。`);
    } catch (error) {
      setNotice(`披露版报告下载失败：${String(error)}`);
    }
  }

  async function downloadReproducibilityBundle() {
    if (!selectedTask) return;
    setNotice("");
    try {
      const response = await apiFetch(`/research/tasks/${selectedTask.id}/reproducibility.json`);
      if (!response.ok) { const payload = await response.json(); throw new Error(errorMessage(payload, "复现包下载失败")); }
      saveBlobAsFile(await response.blob(), `factor-run-${selectedTask.id.slice(0, 8)}.json`);
    } catch (error) { setNotice(String(error)); }
  }

  async function downloadHistoricalAudit(table: "daily" | "unlabeled", runId = task?.id) {
    if (!runId) return;
    setNotice("");
    try {
      const response = await apiFetch(`/research/tasks/${runId}/historical-audit/${table}.csv`);
      if (!response.ok) { const payload = await response.json(); throw new Error(errorMessage(payload, "审计 CSV 下载失败")); }
      saveBlobAsFile(await response.blob(), `historical-audit-${table}-${runId.slice(0, 8)}.csv`);
    } catch (error) { setNotice(String(error)); }
  }

  async function taskAction(action: "cancel" | "retry") {
    if (!selectedTask) return;
    setLoading(true); setNotice("");
    try {
      const response = await apiFetch(`/research/tasks/${selectedTask.id}/${action}`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, action === "cancel" ? "取消失败" : "重试失败"));
      setNotice(action === "cancel" ? "取消请求已提交" : "已创建新的重试任务");
      await loadTasks();
      if (action === "retry") setSelectedTaskId(payload.id);
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  function toggleComparisonRun(id: string) {
    comparisonSession.current += 1;
    setComparisonLoading(false);
    setComparison(null);
    setNotice("");
    setComparisonRunIds(current => current.includes(id) ? current.filter(item => item !== id) : current.length < 6 ? [...current, id] : current);
  }

  async function runComparison() {
    if (comparisonRunIds.length < 2) return;
    const session = ++comparisonSession.current;
    const isCurrent = () => comparisonSession.current === session;
    const runIds = [...comparisonRunIds];
    setComparisonLoading(true); setNotice("");
    try {
      const payload = await resolveCurrentComparison(async () => {
        const response = await apiFetch("/research/comparisons", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_ids: runIds }) });
        const value = await response.json();
        if (!response.ok) throw new Error(errorMessage(value, "实验对比失败"));
        return value as Comparison;
      }, isCurrent);
      if (payload) setComparison(payload);
    } catch (error) { if (isCurrent()) setNotice(String(error)); }
    finally { if (isCurrent()) setComparisonLoading(false); }
  }

  async function downloadComparison(format: "csv" | "html") {
    if (!comparison || comparisonRunIds.length < 2) return;
    const session = ++comparisonSession.current;
    const isCurrent = () => comparisonSession.current === session;
    const runIds = [...comparisonRunIds];
    setComparisonLoading(true); setNotice("");
    try {
      const blob = await resolveCurrentComparison(async () => {
        const response = await apiFetch(`/research/comparisons/export.${format}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_ids: runIds }) });
        if (!response.ok) { const payload = await response.json(); throw new Error(errorMessage(payload, "对比文件导出失败")); }
        return response.blob();
      }, isCurrent);
      if (!blob) return;
      saveBlobAsFile(blob, comparisonDownloadFilename(format, runIds));
    } catch (error) { if (isCurrent()) setNotice(String(error)); }
    finally { if (isCurrent()) setComparisonLoading(false); }
  }

  function downloadComparisonJson() {
    if (!comparison || comparisonLoading) return;
    const runIds = comparison.items.map(item => item.run_id);
    const blob = new Blob([comparisonJsonContent(comparison)], { type: "application/json;charset=utf-8" });
    saveBlobAsFile(blob, comparisonDownloadFilename("json", runIds));
  }

  async function createPlatformUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setNotice("");
    const form = event.currentTarget; const data = new FormData(form);
    try {
      const response = await apiFetch("/users", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: data.get("username"), display_name: data.get("display_name"), password: data.get("password"), role: data.get("role") }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "创建用户失败"));
      form.reset(); setNotice(`账号 ${payload.username} 已创建`); await loadUsers();
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  async function updatePlatformUser(id: string, changes: Record<string, unknown>) {
    setLoading(true); setNotice("");
    try {
      const response = await apiFetch(`/users/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes) });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "更新用户失败"));
      setNotice(`账号 ${payload.username} 已更新`); await loadUsers();
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  if (!authChecked) return <div className="login-page"><div className="login-card"><div className="brand dark"><span>FL</span><strong>FactorLab</strong></div><p>正在验证会话…</p></div></div>;
  if (!user) return <div className="login-page"><form className="login-card" onSubmit={login}><div className="brand dark"><span>FL</span><strong>FactorLab</strong></div><p className="eyebrow">PRIVATE RESEARCH PLATFORM</p><h1>登录研究平台</h1>{notice && <div className="error">{notice}</div>}<label>用户名<input name="username" autoComplete="username" required defaultValue="admin" /></label><label>密码<input name="password" type="password" autoComplete="current-password" required /></label><button disabled={loading}>{loading ? "登录中…" : "登录"}</button><small>演示账号由部署环境初始化，请勿在生产环境使用默认密码。</small></form></div>;

  const canResearch = user.role !== "viewer";
  const isAdmin = user.role === "admin";
  const factorName = (key: string) => factors.find(item => item.id === key)?.name ?? key;
  const comparisonMetrics = [["coverage", "有效观测", false], ["ic_mean", "IC均值", false], ["rank_ic_mean", "Rank IC", false], ["icir", "ICIR", false], ["ic_positive_ratio", "IC为正", true], ["long_short_total_return", "毛多空累计收益", true], ["long_short_net_total_return", "成本后多空累计收益", true], ["top_group_turnover", "头部组换手", true]] as const;
  function toggleCompositeFactor(key: string) {
    setCompositeFactors(current => current.includes(key) ? current.filter(item => item !== key) : current.length < 6 ? [...current, key] : current);
  }
  return <div className="shell"><aside><div className="brand"><span>FL</span><strong>FactorLab</strong></div><nav><button className={view === "dashboard" ? "active" : ""} onClick={() => { setView("dashboard"); loadDashboard().catch(() => undefined); }}>项目总览</button><button className={view === "research" ? "active" : ""} onClick={() => setView("research")}>研究工作台</button><button className={view === "datasets" ? "active" : ""} onClick={() => setView("datasets")}>数据集</button><button className={view === "factors" ? "active" : ""} onClick={() => setView("factors")}>因子库</button><button className={view === "tasks" ? "active" : ""} onClick={() => setView("tasks")}>任务中心</button><button className={view === "comparisons" ? "active" : ""} onClick={() => { setComparisonCandidatesLoading(true); setView("comparisons"); }}>实验对比</button><button className={view === "reports" ? "active" : ""} onClick={() => { setReportListLoading(true); setView("reports"); }}>报告中心</button>{isAdmin && <button className={view === "users" ? "active" : ""} onClick={() => setView("users")}>用户管理</button>}</nav><div className="account"><strong>{user.display_name}</strong><span>{user.role}</span><button onClick={logout}>退出登录</button></div><p className="scope">课程验收版 · 沪深 A 股日频</p></aside>
    <main>{notice && <div className="notice">{notice}</div>}{view === "dashboard" ? <>
      <header><div><p className="eyebrow">PROJECT OVERVIEW · {dashboard?.scope === "personal" ? "PERSONAL" : "GLOBAL"}</p><h1>研究平台运行概览</h1><p>{dashboard?.scope === "personal" ? "展示共享研究资源和你创建的任务与报告。" : "展示平台共享资源及全部研究活动。"}</p></div><button onClick={() => setView("research")} disabled={!canResearch}>{canResearch ? "新建研究" : "只读访问"}</button></header>
      <section className="overview-metrics"><article className="card"><label>已发布数据</label><b>{dashboard?.datasets.published ?? "—"}</b><small>草稿 {dashboard?.datasets.draft ?? 0} · 共 {dashboard?.datasets.total ?? 0} 个版本</small></article><article className="card"><label>内置因子</label><b>{dashboard?.factors.builtin ?? "—"}</b><small>支持等权多因子合成</small></article><article className="card"><label>研究任务</label><b>{dashboard?.tasks.total ?? "—"}</b><small>成功率 {number(dashboard?.tasks.success_rate, true)}</small></article><article className="card"><label>研究报告</label><b>{dashboard?.reports.total ?? "—"}</b><small>成功任务自动归档</small></article></section>
      <section className="overview-grid"><article className="card status-overview"><div className="section-title"><div><p className="eyebrow">TASK HEALTH</p><h2>任务状态分布</h2></div><button onClick={() => setView("tasks")}>查看全部</button></div>{["success","running","pending","failed","cancelled"].map(status => { const count = dashboard?.tasks.by_status[status] ?? 0; const total = dashboard?.tasks.total || 1; return <div className="status-row" key={status}><span>{statusLabel(status)}</span><div><i className={status} style={{width: `${count / total * 100}%`}} /></div><b>{count}</b></div>; })}</article><article className="card recent-activity"><div className="section-title"><div><p className="eyebrow">RECENT RUNS</p><h2>近期研究活动</h2></div></div>{dashboard?.recent_tasks.map(item => <button key={item.id} onClick={() => { setSelectedTaskId(item.id); setView("tasks"); }}><span className={`status ${item.status}`}>{statusLabel(item.status)}</span><b>{item.experiment_name}</b><small>{formatTime(item.queued_at)}</small></button>)}{!dashboard?.recent_tasks.length && <div className="empty">尚无研究任务，从研究工作台开始第一次运行。</div>}</article></section>
      <section className="card platform-scope"><div><p className="eyebrow">CURRENT SCOPE</p><h2>沪深 A 股 · 日频 · 私有部署</h2></div><span>最新数据：{dashboard?.datasets.latest_name ?? "暂无"}</span><span>研究结果仅用于课程研究，不构成投资建议</span></section>
    </> : view === "research" ? <>
      <header><div><p className="eyebrow">RESEARCH WORKSPACE</p><h1>把因子想法变成可复现的证据</h1><p>固定数据版本、因子口径与检验参数，一次运行保留完整研究轨迹。</p></div><button onClick={runResearch} disabled={loading || !canResearch || !selected || !!researchValidationError || (researchMode === "single" ? !selectedFactor : researchMode === "composite" ? compositeFactors.length < 2 : false)}>{!canResearch ? "只读模式" : loading ? "正在运行…" : "运行研究"}</button></header>
      {researchValidationError && <div className="notice" role="alert">当前配置不能提交：{researchValidationError}</div>}
      <div className="workspace-step"><span>01</span><div><h2>配置研究</h2><p>先选研究模式与数据版本，再确认样本、分组和成本。</p></div></div>
      <div className="mode-switch" role="group" aria-label="研究模式"><button type="button" aria-pressed={researchMode === "single"} className={researchMode === "single" ? "active" : ""} onClick={() => setResearchMode("single")}>单因子检验</button><button type="button" aria-pressed={researchMode === "composite"} className={researchMode === "composite" ? "active" : ""} onClick={() => setResearchMode("composite")}>等权多因子</button><button type="button" aria-pressed={researchMode === "historical"} className={researchMode === "historical" ? "active" : ""} onClick={() => setResearchMode("historical")}>2024 沪深300历史研究</button></div>
      {researchMode === "historical" ? <><section className="config card"><div><label htmlFor="historical-dataset">历史数据包</label><select id="historical-dataset" value={selected?.id ?? ""} onChange={event => setSelectedDataset(event.target.value)}>{eligibleDatasets.map(item => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}</select></div><div><label>因子组合</label><strong>动量20日 · 反转5日 · 波动率20日 · 换手率20日</strong></div><div><label>研究期间</label><strong>2024 年；按日历史成分</strong></div><div><label htmlFor="groups">分组数量</label><input id="groups" type="number" min="2" max="10" value={groups} onChange={event => setGroups(Number(event.target.value))} /></div></section><div className="notice">固定等权、原始数据包价格、MAD 去极值、Z-score 与单边 10 bps 成本假设。结果只是条件研究检验，不代表实际可成交回测。{!selected && " 尚无已发布历史包，请先到数据集页面注册并发布。"}</div></> : <>
      <section className="price-basis card"><label htmlFor="price-basis">价格口径</label><select id="price-basis" value={priceBasis} onChange={event => setPriceBasis(event.target.value as "source_close" | "factor_adjusted")}><option value="source_close">使用导入的 close</option><option value="factor_adjusted">close × adj_factor</option></select><small>若导入价格已经复权，请使用原始导入价格；选择因子调整时，每行必须有正数 adj_factor。</small></section>
      <section className="config card"><div><label htmlFor="dataset">数据版本</label><select id="dataset" value={selected?.id ?? ""} onChange={event => setSelectedDataset(event.target.value)}>{eligibleDatasets.map(item => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}</select></div><div><label htmlFor="factor">研究因子</label>{researchMode === "single" ? <select id="factor" value={selectedFactor?.id ?? ""} onChange={event => { const next = factors.find(item => item.id === event.target.value); setSelectedFactorKey(event.target.value); if (next?.default_lookback) setLookback(next.default_lookback); }}>{factors.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select> : <strong>{compositeFactors.length} 个因子等权合成</strong>}</div><div><label htmlFor="lookback">回看窗口</label>{researchMode === "single" ? selectedFactor?.default_lookback !== null ? <input id="lookback" type="number" min="2" max="120" value={lookback} onChange={event => setLookback(Number(event.target.value))} /> : <strong>当日截面</strong> : <strong>使用各因子默认窗口</strong>}</div><div><label htmlFor="groups">分组数量</label><input id="groups" type="number" min="2" max="10" value={groups} onChange={event => setGroups(Number(event.target.value))} /><small>t 日因子 → t+1 收益</small></div></section>
      {selectedWeekendDatasetAlert(selected) && <div className="notice" role="alert">当前选择的数据版本 {selected.name}（{selected.dataset_key} · {selected.version}）含 {selected.quality_report.weekend_date_count} 个周末日期、{selected.quality_report.weekend_row_count} 行行情。请先核对源文件；这不是完整交易所日历校验，系统不会自动删行或禁止运行。</div>}
      {importedCsvProvenanceNotice(selected) && <div className="notice" role="note">{importedCsvProvenanceNotice(selected)}</div>}
      {isKnownSyntheticDemo(selected) && <div className="notice" role="note">当前内置演示版本按工作日生成，并非真实沪深交易日历；只读复核发现其含公告休市日行情。此数据与研究收益仅用于软件功能验收，不可作为真实市场证据。</div>}
      {selected && calendarDatasetAlerts([selected]).length > 0 && <div className="notice" role="alert">当前数据版本的公告休市核对：{(selected.quality_report.announced_weekday_closure_row_count ?? 0) > 0 ? `${selected.quality_report.announced_weekday_closure_date_count} 个公告休市工作日、${selected.quality_report.announced_weekday_closure_row_count} 行行情（${selected.quality_report.announced_weekday_closure_dates?.join("、") || "日期见质量报告"}）` : "未发现已覆盖年份内的公告休市工作日行情"}。{(selected.quality_report.calendar_uncovered_years?.length ?? 0) > 0 && `${selected.quality_report.calendar_uncovered_years?.join("、")} 年未覆盖。`}仅作人工复核，不自动删行或证明其他日期均为交易日。</div>}
      <section className="sample-config card"><div><label htmlFor="sample-start">因子起始日</label><input id="sample-start" type="date" min={selected?.start_date ?? undefined} max={sampleEnd || selected?.end_date || undefined} value={sampleStart} onChange={event => setSampleStart(event.target.value)} /></div><div><label htmlFor="sample-end">因子结束日</label><input id="sample-end" type="date" min={sampleStart || selected?.start_date || undefined} max={selected?.end_date ?? undefined} value={sampleEnd} onChange={event => setSampleEnd(event.target.value)} /></div><div><label htmlFor="sample-symbols">证券样本（可选）</label><input id="sample-symbols" value={sampleSymbols} onChange={event => setSampleSymbols(event.target.value)} placeholder="留空表示全部；多个代码用逗号分隔" /></div><small>因子计算会读取起始日前所需历史，但结果只保留所选日期。</small></section>
      <section className="sample-config card"><div><label htmlFor="validation-start">验证期起始日（可选）</label><input id="validation-start" type="date" min={sampleStart || selected?.start_date || undefined} max={sampleEnd || selected?.end_date || undefined} value={validationStart} onChange={event => setValidationStart(event.target.value)} /></div><small>填写后按信号日期切分研究期与验证期，并隔离边界前最后一个信号日，防止其下一日收益跨入验证期。请在运行前确定日期；事后调整不构成真正的前瞻样本外验证。</small></section>
      {researchMode === "composite" && <section className="factor-picker card"><div><strong>选择成分因子</strong><small>至少2个；先分别进行截面预处理，再取共同样本等权合成。</small></div>{factors.map(item => <label key={item.id}><input type="checkbox" checked={compositeFactors.includes(item.id)} onChange={() => toggleCompositeFactor(item.id)} /><span>{item.name}</span><small>{item.default_lookback ? `${item.default_lookback}日` : "当日"}</small></label>)}</section>}
      <section className="preprocess card"><strong>截面预处理</strong><label><input type="checkbox" checked={winsorize} onChange={event => setWinsorize(event.target.checked)} /> MAD 3倍去极值</label><label><input type="checkbox" checked={standardize} onChange={event => setStandardize(event.target.checked)} /> Z-score标准化</label><label className="cost-input">单边成本 <input type="number" min="0" max="100" step="1" value={transactionCostBps} onChange={event => setTransactionCostBps(Number(event.target.value))} /> bps</label><small>按多空两边实际成员换手扣减固定成本。</small></section></>}
      {rawTask && !task && <div className="notice" role="status">研究配置已改变，工作台已隐藏旧任务的指标与图表。旧结果仍可在任务中心按 Run ID 查看；请重新运行当前配置。</div>}
      {task?.id && task.id !== "local-error" && <div className="result-provenance" role="status">当前结果绑定 Run <code>{task.id.slice(0, 8)}</code> · 数据版本 {task.dataset_version ?? "处理中"} · {statusLabel(task.status)}</div>}
      <section className="metrics"><article className="card"><label>有效观测</label><b>{task?.result?.coverage ?? "—"}</b><small>股票 × 交易日</small></article><article className="card"><label>IC 均值</label><b>{number(task?.result?.ic_mean)}</b><small>Pearson 相关</small></article><article className="card"><label>Rank IC</label><b>{number(task?.result?.rank_ic_mean)}</b><small>Spearman 相关</small></article><article className="card"><label>ICIR</label><b>{number(task?.result?.icir)}</b><small>未年化</small></article><article className="card"><label>IC为正比例</label><b>{number(task?.result?.ic_positive_ratio, true)}</b><small>方向稳定性</small></article><article className="card"><label>毛多空累计收益</label><b>{number(task?.result?.long_short_total_return, true)}</b><small>{longShortGroupLabel(groups)}</small></article><article className="card"><label>成本后多空收益</label><b>{number(task?.result?.long_short_net_total_return, true)}</b><small>单边 {task?.result?.transaction_cost_bps ?? transactionCostBps} bps</small></article><article className="card"><label>多空双边换手</label><b>{number(task?.result?.long_short_turnover, true)}</b><small>包含首次建仓</small></article></section>
      <section className="card result"><div className="section-title"><div><p className="eyebrow">QUANTILE RETURN</p><h2>分组平均下一日收益</h2></div><span className={`status ${task?.status ?? "idle"}`}>{task?.status === "success" ? "计算完成" : task?.status === "failed" ? "运行失败" : task ? `${task.progress ?? 0}%` : "等待运行"}</span></div>{task?.error_summary && <p className="error">{task.error_summary}</p>}{task?.result?.group_returns.length ? <div className="bars">{task.result.group_returns.map(item => <div className="bar-row" key={item.group}><span>Q{item.group}</span><div><i style={{width: `${Math.min(100, Math.abs(item.mean_return) * 4000 + 8)}%`}} /></div><strong>{number(item.mean_return, true)}</strong></div>)}</div> : <div className="empty">{task?.result ? "本次没有可计算的分组收益；空值不代表零收益。" : "尚无当前配置的分组结果；未计算不代表零收益。"}</div>}</section>
      <div className="workspace-step results-step"><span>02</span><div><h2>图表与诊断</h2><p>先看关键指标与分组收益，再结合时间序列和限制解释结果。</p></div></div>
      {(task?.result?.group_skipped_constant_factor_days ?? 0) > 0 && <div className="notice">有 {task!.result!.group_skipped_constant_factor_days} 个交易日全截面因子同值：IC 不可计算，分组与多空收益未生成；图表仅展示其余可分组日期。</div>}
      {(task?.result?.group_skipped_insufficient_sample_days ?? 0) > 0 && <div className="notice">有 {task!.result!.group_skipped_insufficient_sample_days} 个交易日有效证券数少于分组数：未生成分组与多空收益，IC 可计算时仍保留。</div>}
      {task?.result?.time_split && <section className="card comparison-table"><h2>研究期／验证期 IC 诊断</h2><p>验证期从 {task.result.time_split.validation_start_date} 开始；边界前 {task.result.time_split.embargo_signal_date} 的信号已隔离。全区间指标仍单独保留；这里只比较 IC，不是可交易收益或前瞻有效性证明。</p><div className="preview-scroll"><table><thead><tr><th>阶段</th><th>日期</th><th>观测</th><th>有效 IC 日</th><th>IC 均值</th><th>Rank IC</th><th>ICIR</th><th>IC 为正</th></tr></thead><tbody>{([ ["研究期", task.result.time_split.research], ["验证期", task.result.time_split.validation] ] as const).map(([label, item]) => <tr key={label}><td>{label}</td><td>{item.start_date} 至 {item.end_date}</td><td>{item.observation_count}</td><td>{item.valid_ic_dates}</td><td>{number(item.ic_mean)}</td><td>{number(item.rank_ic_mean)}</td><td>{number(item.icir)}</td><td>{number(item.ic_positive_ratio, true)}</td></tr>)}</tbody></table></div></section>}
      {!!task?.result?.daily_coverage?.length && <DailyCoverageTable key={task.id} runId={task.id} rows={task.result.daily_coverage} candidateCoverage={task.result.candidate_coverage} coverage={task.result.coverage} coverageRatio={task.result.coverage_ratio} zeroObservationDays={task.result.zero_observation_days} />}
      {task?.result && <SavedSeriesCharts runId={task.id} result={task.result} onDownloadLongShort={downloadLongShort} onDownloadGroupNav={downloadGroupNav} />}
      {task?.result?.composite && <section className="card composite-result"><div className="section-title"><div><p className="eyebrow">COMPOSITE DIAGNOSTICS</p><h2>多因子合成诊断</h2></div><strong>共同样本 {task.result.composite.common_coverage}</strong></div><div className="weight-list">{Object.entries(task.result.composite.weights).map(([key, value]) => <span key={key}><b>{factorName(key)}</b>{number(value, true)}<small>原始覆盖 {task.result!.composite!.component_coverage[key]}</small></span>)}</div><h3>因子相关矩阵</h3><div className="correlation-table">{task.result.composite.correlation_matrix.map(item => <span key={`${item.left}-${item.right}`}><b>{factorName(item.left)} × {factorName(item.right)}</b>{number(item.correlation)}</span>)}</div></section>}
      {task?.result?.historical_audit && <section className="card historical-audit"><div className="section-title"><div><p className="eyebrow">HISTORICAL AUDIT</p><h2>历史股票池与标签审计</h2></div><strong>2024 沪深300</strong></div><p>逐日按历史成分及交易状态筛选；下一日收益缺失不填零、不跳至复牌日。以下是研究样本检验，并非真实可成交收益。</p><div className="preview-scroll"><table><thead><tr><th>因子</th><th>候选</th><th>有效信号</th><th>有效收益</th><th>窗口无效</th><th>次日不可用</th></tr></thead><tbody>{Object.entries(task.result.historical_audit).map(([key, item]) => <tr key={key}><td>{factorName(key)}</td><td>{item.totals.candidate_count ?? 0}</td><td>{item.totals.factor_signal ?? 0}</td><td>{item.totals.valid_return ?? 0}</td><td>{item.totals.invalid_contiguous_window ?? 0}</td><td>{item.unlabeled_signals.length}</td></tr>)}</tbody></table></div><div className="task-actions"><button onClick={() => downloadHistoricalAudit("daily")}>下载逐日审计 CSV</button><button onClick={() => downloadHistoricalAudit("unlabeled")}>下载无标签信号 CSV</button></div><small>完整逐日计数及无标签信号的证券、日期、因子值和原因也保存在任务结果与复现包中。</small></section>}
    </> : view === "factors" ? <>
      <header><div><p className="eyebrow">FACTOR CATALOG</p><h1>六个内置因子，统一口径与版本</h1><p>每个因子明确公式、字段依赖和默认窗口，研究任务会固定因子版本。</p></div></header>
      <section className="factor-grid">{factors.map(item => <article className={`card factor-card ${selectedFactor?.id === item.id ? "selected" : ""}`} key={item.id} onClick={() => { setSelectedFactorKey(item.id); if (item.default_lookback) setLookback(item.default_lookback); }}><div className="section-title"><span className="factor-category">{item.category}</span><small>v{item.version}</small></div><h2>{item.name}</h2><p>{item.description}</p><code>{item.formula}</code><div><label>所需字段</label><span>{item.required_columns.join(" · ")}</span></div><button onClick={() => { setResearchMode("single"); setView("research"); }}>用于研究</button></article>)}</section>
    </> : view === "datasets" ? <>
      <header><div><p className="eyebrow">DATA GOVERNANCE</p><h1>每一次研究，从确定的数据版本开始</h1><p>导入日行情 CSV 或注册封存的历史数据包，核验后发布为研究输入。</p></div></header>
      {(weekendDatasetAlerts(datasets).length > 0 || calendarDatasetAlerts(datasets).length > 0 || datasets.some(isKnownSyntheticDemo)) &&
        <section className="dataset-alerts" aria-label="数据版本日期提醒">
          <h2>需要核对的日期</h2>
          {weekendDatasetAlerts(datasets).map(item =>
            <p className="notice" key={`weekend-${item.id}`}>
              {item.name}（{item.dataset_key} · {item.version}）含 {item.quality_report.weekend_date_count} 个周末日期、{item.quality_report.weekend_row_count} 行行情。请核对源文件；这不是完整交易所日历校验，也未自动删行。
            </p>) }
          {calendarDatasetAlerts(datasets).map(item => <p className="notice" key={`closure-${item.id}`}>{item.name}（{item.dataset_key} · {item.version}）公告休市核对：{(item.quality_report.announced_weekday_closure_row_count ?? 0) > 0 && `${item.quality_report.announced_weekday_closure_date_count} 个休市工作日、${item.quality_report.announced_weekday_closure_row_count} 行行情；`}{(item.quality_report.calendar_uncovered_years?.length ?? 0) > 0 && `${item.quality_report.calendar_uncovered_years?.join("、")} 年未覆盖；`}请人工核对。版本 {item.quality_report.announced_closure_calendar_version ?? "未知"}；此项不是完整开市日认证。</p>)}
          {datasets.filter(isKnownSyntheticDemo).map(item => <p className="notice" key={`demo-calendar-${item.id}`}>{item.name}（{item.dataset_key} · {item.version}）是内置合成演示数据：按工作日生成而非真实沪深交易日历。只读复核发现 11 个公告休市工作日、220 行行情；仅用于软件功能验收，不作为真实市场研究证据。</p>)}
        </section>}
      {datasets.some(item => importedCsvProvenanceNotice(item) !== null) && <div className="notice" role="note">普通 CSV 数据版本的质量检查不认证来源真实性、使用授权或完整交易日历；发布前请核对原始来源和交易所记录。</div>}
      {calendarPreviewDetails && <div className="notice" role="alert">导入前日历核对：{calendarPreviewDetails}</div>}
      {isAdmin ? <><form className="card upload adapted-upload" onSubmit={uploadDataset}><div><label htmlFor="dataset_key">数据集标识</label><input id="dataset_key" name="dataset_key" required pattern="[a-z][a-z0-9_]{2,49}" placeholder="例如 csi300_daily" /></div><div><label htmlFor="name">显示名称</label><input id="name" name="name" required placeholder="例如 沪深300日行情" /></div><div><label htmlFor="file">CSV文件</label><input id="file" name="file" type="file" accept=".csv,text/csv" required onChange={() => { if (adapterPreviewAttempted) setAdapterPreviewInvalidated(true); setAdapterPreview(null); }} /></div><label className="adapter-toggle"><input name="normalize_cn_csv" type="checkbox" value="true" /> 自动适配常见A股字段</label><button type="button" className="secondary" onClick={previewAdapter} disabled={loading}>适配预览</button><button disabled={loading}>{loading ? "处理中…" : "导入并检查"}</button></form>{adapterPreview && <section className="card adapter-preview"><div className="section-title"><div><p className="eyebrow">CN CSV ADAPTER</p><h2>标准化预览</h2></div><span>{adapterPreview.report.converted_rows} 行 · {adapterPreview.report.source_encoding}</span></div><p>预览原文件 SHA-256：{adapterPreview.source_sha256}</p><div className="mapping-list">{Object.entries(adapterPreview.report.column_mapping).map(([source, target]) => <span key={source}><b>{source}</b> → {target}</span>)}</div>{adapterPreview.report.dropped_columns.length > 0 && <p>未导入字段：{adapterPreview.report.dropped_columns.join("、")}</p>}<div className="preview-scroll"><table><thead><tr>{Object.keys(adapterPreview.preview[0] ?? {}).map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{adapterPreview.preview.map((row, index) => <tr key={index}>{Object.keys(row).map(column => <td key={column}>{row[column]}</td>)}</tr>)}</tbody></table></div><ul>{adapterPreview.report.warnings.map(item => <li key={item}>{item}</li>)}</ul></section>}</> : <div className="notice">当前角色可以查看数据版本，但只有管理员可以导入和发布。</div>}
      {isAdmin && <form className="card bundle-registration" onSubmit={registerHistoricalBundle}><div><p className="eyebrow">SEALED HISTORICAL BUNDLE</p><h2>注册本机历史数据包</h2><small>先将私有包放在 DATA_ROOT 同级的 real/bundles 目录；输入包 ID 注册草稿，核对后再发布。</small></div><label htmlFor="bundle-id">包 ID<input id="bundle-id" value={bundleId} onChange={event => setBundleId(event.target.value)} placeholder="hs300_2024_…" pattern="hs300_2024_[0-9a-f]{16}" required /></label><button disabled={loading}>{loading ? "校验中…" : "注册历史包"}</button></form>}
      <section className="dataset-list">{datasets.map(item => <article className="card dataset" key={item.id}><div className="section-title"><div><p className="eyebrow">{item.dataset_key}</p><h2>{item.name}</h2></div><span className={`status ${item.status === "published" ? "success" : "idle"}`}>{item.status === "published" ? "已发布" : "草稿"}</span></div><div className="dataset-stats"><span><b>{item.row_count}</b> 行</span><span><b>{item.symbol_count}</b> 只证券</span><span><b>{item.start_date ?? "—"}</b> 起始</span><span><b>{item.end_date ?? "—"}</b> 结束</span></div><div className="quality-summary">{isHistoricalDataset(item) ? <><span><b>{item.quality_report.verified_files ?? "—"}</b>已校验文件</span><span><b>{item.quality_report.member_trading_days ?? "—"}</b>历史成员日</span><span><b>整包摘要</b>非逐字段质量检查</span></> : <><span><b>{item.quality_report.columns?.length ?? 3}</b>字段</span><span><b>{Object.values(item.quality_report.missing_counts ?? {}).reduce((sum, value) => sum + value, 0)}</b>缺失单元格</span><span><b>{item.quality_report.valid === false ? "异常" : "通过"}</b>质量检查</span><span><b>{item.quality_report.internal_calendar_gap_count ?? "—"}</b>活跃期缺日</span></>}</div>{!isHistoricalDataset(item) && (item.quality_report.internal_calendar_gap_count ?? 0) > 0 && <p className="notice">推断日历中有 {item.quality_report.symbols_with_internal_calendar_gaps} 只证券在自身首末记录之间合计缺少 {item.quality_report.internal_calendar_gap_count} 个证券日；可能涉及停牌或源数据缺行，非导入错误。</p>}<p className="checksum">SHA-256 · {item.checksum}</p><div className="dataset-actions"><span>{item.source_filename} · 版本 {item.version}</span><div><button className="secondary" onClick={() => toggleDatasetPreview(item.id)} disabled={loading}>{datasetPreview?.dataset_id === item.id ? "收起详情" : isHistoricalDataset(item) ? "查看清单摘要" : "质量与预览"}</button>{isAdmin && item.status === "draft" && <button onClick={() => publishDataset(item.id)} disabled={loading}>确认发布</button>}</div></div>{datasetPreview?.dataset_id === item.id && <div className="dataset-preview">{isHistoricalDataset(item) ? <><h3>封存包清单摘要</h3><p>展示包身份与文件计数，不代表对行情字段完整率的逐项检查。</p></> : <><h3>字段完整率</h3><div className="field-quality">{(item.quality_report.columns ?? datasetPreview.columns).map(column => <span key={column}><b>{column}</b><i>{number(item.quality_report.completeness?.[column] ?? 1, true)}</i><small>缺失 {item.quality_report.missing_counts?.[column] ?? 0}</small></span>)}</div>{Object.keys(item.quality_report.numeric_summary ?? {}).length > 0 && <><h3>数值字段范围</h3><div className="numeric-quality">{Object.entries(item.quality_report.numeric_summary ?? {}).map(([column, stats]) => <span key={column}><b>{column}</b><small>最小 {number(stats.min)}</small><small>均值 {number(stats.mean)}</small><small>最大 {number(stats.max)}</small></span>)}</div></>}</>}<h3>{isHistoricalDataset(item) ? "清单项目" : `前 ${datasetPreview.preview_count} 行预览`}</h3><div className="preview-scroll"><table><thead><tr>{datasetPreview.columns.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{datasetPreview.rows.map((row, index) => <tr key={index}>{datasetPreview.columns.map(column => <td key={column}>{row[column] || <em>空</em>}</td>)}</tr>)}</tbody></table></div>{datasetPreview.truncated && <small>仅展示前 {datasetPreview.preview_count} 行，共 {datasetPreview.total_rows} 行。</small>}</div>}</article>)}{!datasets.length && <div className="empty card">尚无数据版本。</div>}</section>
    </> : view === "tasks" ? <>
      <header><div><p className="eyebrow">RUN REGISTRY</p><h1>每次运行都有状态，也有来路</h1><p>查看任务进度、失败原因、版本绑定与不可变研究结果。运行中每 2 秒刷新，全部结束后每 30 秒刷新。</p></div><button onClick={() => loadTasks()} disabled={loading}>刷新任务</button></header>
      <section className="card task-filters"><label>检索任务<input type="search" value={taskQuery} onChange={event => setTaskQuery(event.target.value)} placeholder="Run ID 或研究名称" /></label><label>任务状态<select value={taskStatusFilter} onChange={event => setTaskStatusFilter(event.target.value as TaskStatusFilter)}><option value="all">全部状态</option><option value="success">成功</option><option value="running">运行中</option><option value="pending">等待中</option><option value="failed">失败</option><option value="cancelled">已取消</option></select></label><span aria-live="polite">显示 {visibleTasks.length}/{tasks.length} 项任务</span></section>
      <section className="task-layout">
        <div className="card task-list">{visibleTasks.map(item => <button key={item.id} className={selectedTask?.id === item.id ? "selected" : ""} onClick={() => setSelectedTaskId(item.id)}><span className={`status ${item.status}`}>{statusLabel(item.status)}</span><strong>{item.experiment_name ?? "研究任务"}</strong><small>{formatTime(item.queued_at)}</small><i><b style={{width: `${item.progress ?? 0}%`}} /></i></button>)}{!tasks.length ? <div className="empty">尚无研究任务。</div> : !visibleTasks.length && <div className="empty">没有符合检索和状态条件的任务。</div>}</div>
        <div className="card task-detail">{selectedTask ? <><div className="section-title"><div><p className="eyebrow">RUN · {selectedTask.id.slice(0, 8)}</p><h2>{selectedTask.experiment_name}</h2></div><div className="task-actions"><span className={`status ${selectedTask.status}`}>{statusLabel(selectedTask.status)}</span><button onClick={downloadReproducibilityBundle}>下载复现包</button>{selectedTask.status === "success" && <button onClick={openSelectedTaskReport}>查看同 Run 报告</button>}{canResearch && (selectedTask.status === "pending" || selectedTask.status === "running") && <button onClick={() => taskAction("cancel")} disabled={loading || Boolean(selectedTask.cancellation_requested_at)}>{selectedTask.cancellation_requested_at ? "等待取消" : "取消任务"}</button>}{canResearch && (selectedTask.status === "failed" || selectedTask.status === "cancelled") && <button onClick={() => taskAction("retry")} disabled={loading}>重新运行</button>}</div></div>
          {selectedTask.error_summary && <p className="error">{selectedTask.error_summary}</p>}
          <div className="repro-grid"><span><label>数据版本</label><b>{selectedTask.dataset_version}</b><small>{selectedTask.dataset_version_id}</small></span><span><label>因子版本</label><b>{selectedTask.factor_version}</b><small>{selectedTask.factor_version_id}</small></span><span><label>代码版本</label><b>{selectedTask.code_version}</b><small>实验创建时固定</small></span><span><label>执行时间</label><b>{formatTime(selectedTask.started_at)}</b><small>结束：{formatTime(selectedTask.finished_at)}</small></span></div>
          <h3>研究参数</h3><pre>{JSON.stringify(selectedTask.parameters, null, 2)}</pre>
          {selectedTask.result && <div className="task-actions task-series-export"><button className="secondary" onClick={() => saveBlobAsFile(new Blob([icSeriesCsv(selectedTask.id, selectedTask.result!.ic_series)], { type: "text/csv;charset=utf-8" }), icSeriesFilename(selectedTask.id))}>下载每日 IC CSV</button><button className="secondary" onClick={() => downloadLongShort(selectedTask.id, selectedTask.result!)}>下载多空逐日 CSV</button><button className="secondary" onClick={() => downloadGroupNav(selectedTask.id, selectedTask.result!)}>下载各组逐日净值 CSV</button><small>按各自有效日期导出原值，空值不补零；与当前 Run 的复现包同源。</small></div>}
          {selectedTask.result && <details className="task-series-charts" key={selectedTask.id}><summary>查看此 Run 的逐日曲线</summary><p>仅回看该 Run 保存的 IC、多空和各组净值；毛／成本后口径与上方下载文件一致，不重新运行研究。</p><SavedSeriesCharts runId={selectedTask.id} result={selectedTask.result} onDownloadLongShort={downloadLongShort} onDownloadGroupNav={downloadGroupNav} showActions={false} includeDistribution={false} /></details>}
          {selectedTask.result && <><div className="compact-metrics"><span><label>有效观测</label><b>{selectedTask.result.coverage}</b></span><span><label>IC均值</label><b>{number(selectedTask.result.ic_mean)}</b></span><span><label>Rank IC</label><b>{number(selectedTask.result.rank_ic_mean)}</b></span><span><label>ICIR</label><b>{number(selectedTask.result.icir)}</b></span><span><label>毛多空收益</label><b>{number(selectedTask.result.long_short_total_return, true)}</b></span><span><label>成本后多空收益</label><b>{number(selectedTask.result.long_short_net_total_return, true)}</b></span></div><h3>分组平均收益</h3><div className="bars">{selectedTask.result.group_returns.map(item => <div className="bar-row" key={item.group}><span>Q{item.group}</span><div><i style={{width: `${Math.min(100, Math.abs(item.mean_return) * 4000 + 8)}%`}} /></div><strong>{number(item.mean_return, true)}</strong></div>)}</div></>}
          {visibleTaskConclusion && <section className={`conclusion ${visibleTaskConclusion.grade}`}><div className="section-title"><div><p className="eyebrow">RULE-BASED DRAFT · v{visibleTaskConclusion.method.version}</p><h3>结构化研究结论</h3></div><span>{visibleTaskConclusion.grade}</span></div><strong>{visibleTaskConclusion.headline}</strong><div className="conclusion-columns"><div><h3>支持证据</h3><ul>{visibleTaskConclusion.evidence.map(item => <li key={item}>{item}</li>)}</ul></div><div><h3>限制条件</h3><ul>{visibleTaskConclusion.limitations.map(item => <li key={item}>{item}</li>)}</ul></div><div><h3>建议下一步</h3><ol>{visibleTaskConclusion.next_steps.map(item => <li key={item}>{item}</li>)}</ol></div></div><small>{visibleTaskConclusion.disclaimer}</small></section>}
          <h3>执行日志</h3><div className="run-logs">{visibleTaskLogs?.map(item => <div className={item.level} key={item.id}><time>{formatTime(item.created_at)}</time><b>{item.event}</b><span>{item.message}</span></div>)}{visibleTaskLogs === null ? <div className="empty">正在加载日志…</div> : visibleTaskLogs.length === 0 && <div className="empty">暂无日志。</div>}</div>
        </> : <div className="empty">从左侧选择一项任务查看详情。</div>}</div>
      </section>
      {!!selectedTask?.result?.daily_coverage?.length && <DailyCoverageTable key={selectedTask.id} runId={selectedTask.id} rows={selectedTask.result.daily_coverage} candidateCoverage={selectedTask.result.candidate_coverage} coverage={selectedTask.result.coverage} coverageRatio={selectedTask.result.coverage_ratio} zeroObservationDays={selectedTask.result.zero_observation_days} />}
    </> : view === "comparisons" ? <>
      <header><div><p className="eyebrow">EXPERIMENT COMPARISON</p><h1>让历史实验在同一张表里说话</h1><p>选择 2–6 个成功任务；首个选择作为差值基准，系统会检查数据版本、分组数和共同日期。空闲时每 30 秒刷新候选。</p></div><div className="task-actions"><button className="secondary" onClick={() => loadTasks()}>刷新候选</button><button onClick={runComparison} disabled={comparisonLoading || comparisonRunIds.length < 2}>{comparisonLoading ? "对比中…" : `生成对比（${comparisonRunIds.length}）`}</button></div></header>
      <section className="comparison-picker card">{tasks.filter(item => item.status === "success" && item.result).map(item => <label key={item.id} className={comparisonRunIds.includes(item.id) ? "selected" : ""}><input type="checkbox" checked={comparisonRunIds.includes(item.id)} onChange={() => toggleComparisonRun(item.id)} disabled={!comparisonRunIds.includes(item.id) && comparisonRunIds.length >= 6} /><span><b>{item.experiment_name}</b><small>{factorName(String(item.parameters?.factor ?? ""))} · {comparisonDatasetLabel(item.dataset_version, item.dataset_version_id)} · {formatTime(item.finished_at)}</small></span></label>)}{comparisonCandidateHint(tasks, comparisonCandidatesLoading) && <div className="empty">{comparisonCandidateHint(tasks, comparisonCandidatesLoading)}</div>}</section>
      {comparison && <><section className={`comparison-summary card ${comparison.comparable ? "ready" : "warning"}`}><div><p className="eyebrow">COMPARABILITY CHECK</p><h2>{comparison.comparable ? "所列口径检查通过，仍属描述性回溯" : "存在口径差异，请谨慎解释"}</h2></div><span>共同 IC 日期 <b>{comparison.common_ic_date_count}</b> · 共同多空分组日期 <b>{comparison.common_group_date_count}</b></span><div className="comparison-downloads"><button onClick={() => downloadComparison("csv")} disabled={comparisonLoading}>下载 CSV</button><button onClick={() => downloadComparison("html")} disabled={comparisonLoading}>下载 HTML 报告</button><button onClick={downloadComparisonJson} disabled={comparisonLoading}>下载 JSON 快照</button></div>{comparison.warnings.map(message => <p key={message}>{message}</p>)}</section><section className="card comparison-table"><div className="preview-scroll"><table><thead><tr><th>指标（原始全区间）</th>{comparison.items.map((item, index) => <th key={item.run_id}>{item.experiment_name}<small>{index === 0 ? "基准" : factorName(item.factor)}</small></th>)}</tr></thead><tbody>{comparisonMetrics.map(([key, label, percent]) => <tr key={key}><th>{label}</th>{comparison.items.map((item, index) => <td key={item.run_id}><b>{key === "coverage" ? item.metrics[key] ?? "—" : number(item.metrics[key], percent)}</b>{index > 0 && <small>较基准 {comparisonDelta(item.delta_from_baseline[key], key === "coverage" ? "count" : percent ? "percent" : "decimal")}</small>}</td>)}</tr>)}</tbody></table></div></section><section className="card comparison-table"><h2>验证期 IC 摘要</h2><p>仅展示已保存的时间切分结果；未切分任务显示为缺失。原始排名不是验证期排名，也不代表同股票样本或验证期收益。{comparison.common_validation_ic_date_count !== null && `共同验证期有效 IC 日：${comparison.common_validation_ic_date_count}。`}</p><div className="preview-scroll"><table><thead><tr><th>验证期</th>{comparison.items.map(item => <th key={item.run_id}>{item.experiment_name}</th>)}</tr></thead><tbody><tr><th>起始日</th>{comparison.items.map(item => <td key={item.run_id}>{item.validation_start_date ?? "—"}</td>)}</tr>{([ ["valid_ic_dates", "有效 IC 日", false], ["ic_mean", "IC 均值", false], ["rank_ic_mean", "Rank IC", false], ["icir", "ICIR", false], ["ic_positive_ratio", "IC 为正", true] ] as const).map(([key, label, percent]) => <tr key={key}><th>{label}</th>{comparison.items.map(item => <td key={item.run_id}>{key === "valid_ic_dates" ? item.validation_ic?.[key] ?? "—" : number(item.validation_ic?.[key], percent)}</td>)}</tr>)}</tbody></table></div></section><section className="comparison-rankings">{Object.entries(comparison.rankings).map(([metric, runIds]) => <article className="card" key={metric}><label>{comparisonMetrics.find(item => item[0] === metric)?.[1] ?? metric} 原始排名</label>{runIds.map((id, index) => { const item = comparison.items.find(value => value.run_id === id); return <span key={id}><b>{index + 1}</b>{item?.experiment_name}</span>; })}</article>)}</section></>}
      {comparison && <div className="notice">共同日期摘要只对齐有效 IC 日期；下方严格样本摘要进一步对齐证券×日期，并在交集截面重算 IC。两者均不重算多空收益或换手；原始指标及排名仍采用各任务全区间。</div>}
      {comparison && <section className="card comparison-table"><h2>共同日期 IC 摘要</h2><p>共同有效 IC 日 {comparison.common_ic_date_count} 天；Rank IC 空值另行排除。</p><div className="preview-scroll"><table><thead><tr><th>指标</th>{comparison.items.map(item => <th key={item.run_id}>{item.experiment_name}</th>)}</tr></thead><tbody>{([ ["ic_mean", "IC 均值", false], ["rank_ic_mean", "Rank IC", false], ["icir", "ICIR", false], ["ic_positive_ratio", "IC 为正", true] ] as const).map(([key, label, percent]) => <tr key={key}><th>{label}</th>{comparison.items.map(item => <td key={item.run_id}>{number(item.common_date_ic[key], percent)}</td>)}</tr>)}<tr><th>Rank IC 有效日</th>{comparison.items.map(item => <td key={item.run_id}>{item.common_date_ic.rank_ic_valid_dates}</td>)}</tr></tbody></table></div></section>}
      {comparison && <section className="card comparison-table"><h2>严格样本 IC 摘要</h2>{comparison.matched_sample.available ? <><p>共同证券×日期观测 {comparison.matched_sample.observation_count} 条，覆盖 {comparison.matched_sample.date_count} 天；次日收益标签差异 {comparison.matched_sample.label_mismatch_count} 条。每个任务按原预处理口径在交集截面重算 IC；不重算多空与交易收益。</p><div className="preview-scroll"><table><thead><tr><th>指标</th>{comparison.items.map(item => <th key={item.run_id}>{item.experiment_name}</th>)}</tr></thead><tbody>{([ ["ic_mean", "IC 均值", false], ["rank_ic_mean", "Rank IC", false], ["icir", "ICIR", false], ["ic_positive_ratio", "IC 为正", true] ] as const).map(([key, label, percent]) => <tr key={key}><th>{label}</th>{comparison.items.map(item => <td key={item.run_id}>{number(comparison.matched_sample.items?.find(value => value.run_id === item.run_id)?.[key], percent)}</td>)}</tr>)}<tr><th>有效 IC 日</th>{comparison.items.map(item => <td key={item.run_id}>{comparison.matched_sample.items?.find(value => value.run_id === item.run_id)?.valid_ic_dates ?? "—"}</td>)}</tr></tbody></table></div></> : <p>{comparison.matched_sample.reason}</p>}</section>}
      {comparison?.matched_sample.available && <p className="comparison-evidence-note">全区间严格样本：最少有效 IC 日 {comparison.matched_sample.min_valid_ic_dates}；{comparison.matched_sample.evidence?.note}</p>}
      {comparison && <section className="card comparison-table"><h2>验证期严格样本 IC 摘要</h2>{comparison.matched_validation_sample.available ? <><p>切分日 {comparison.matched_validation_sample.validation_start_date}；验证期共同证券×日期观测 {comparison.matched_validation_sample.observation_count} 条，覆盖 {comparison.matched_validation_sample.date_count} 天；次日收益标签差异 {comparison.matched_validation_sample.label_mismatch_count} 条。各任务在共同样本上按原预处理口径重算 IC，不重算交易收益。</p><div className="preview-scroll"><table><thead><tr><th>指标</th>{comparison.items.map(item => <th key={item.run_id}>{item.experiment_name}</th>)}</tr></thead><tbody>{([ ["ic_mean", "IC 均值", false], ["rank_ic_mean", "Rank IC", false], ["icir", "ICIR", false], ["ic_positive_ratio", "IC 为正", true] ] as const).map(([key, label, percent]) => <tr key={key}><th>{label}</th>{comparison.items.map(item => <td key={item.run_id}>{number(comparison.matched_validation_sample.items?.find(value => value.run_id === item.run_id)?.[key], percent)}</td>)}</tr>)}<tr><th>有效 IC 日</th>{comparison.items.map(item => <td key={item.run_id}>{comparison.matched_validation_sample.items?.find(value => value.run_id === item.run_id)?.valid_ic_dates ?? "—"}</td>)}</tr></tbody></table></div></> : <p>{comparison.matched_validation_sample.reason}</p>}</section>}
      {comparison?.matched_validation_sample.available && <p className="comparison-evidence-note">验证期严格样本：最少有效 IC 日 {comparison.matched_validation_sample.min_valid_ic_dates}；{comparison.matched_validation_sample.evidence?.note}</p>}
      {comparison && <section className="card comparison-table"><h2>共同样本保留率与产物核对</h2><p>保留率＝所有任务共有的证券×日期观测 ÷ 各任务原观测。原观测与逐股产物条数应一致；不一致会在上方提示。保留率仅披露交集缩小幅度，不设新的合格阈值。</p><div className="preview-scroll"><table><thead><tr><th>任务</th><th>全区间原观测</th><th>产物观测</th><th>全区间保留率</th><th>验证期原观测</th><th>验证期产物观测</th><th>验证期保留率</th></tr></thead><tbody>{comparison.items.map(item => { const full = comparison.matched_sample.items?.find(value => value.run_id === item.run_id); const validation = comparison.matched_validation_sample.items?.find(value => value.run_id === item.run_id); return <tr key={item.run_id}><th>{item.experiment_name}</th><td>{full?.source_observation_count ?? "—"}</td><td>{item.observation_artifact_count ?? "—"}</td><td>{number(full?.retention_ratio, true)}</td><td>{validation?.source_observation_count ?? "—"}</td><td>{item.validation_artifact_count ?? "—"}</td><td>{number(validation?.retention_ratio, true)}</td></tr>; })}</tbody></table></div></section>}
      {comparison && <section className="card comparison-table" style={{marginTop: 16}}><h2>实际研究口径</h2><p className="comparison-scroll-hint">表格可左右滚动，查看完整数据身份与研究口径。</p><div className="preview-scroll"><table><thead><tr><th>任务</th><th>数据版本</th><th>IC日期范围</th><th>证券筛选</th><th>价格口径</th><th>预处理</th><th>代码版本</th></tr></thead><tbody>{comparison.items.map(item => <tr key={item.run_id}><td>{item.experiment_name}<small>{item.run_id.slice(0, 8)}</small></td><td>{item.dataset_version}<small className="comparison-dataset-id">{item.dataset_version_id}</small><small className="comparison-dataset-id">SHA-256 {item.dataset_checksum_sha256}</small></td><td>{item.ic_start_date ?? "—"} 至 {item.ic_end_date ?? "—"}<small>{item.ic_date_count} 个有效截面</small></td><td>{item.sample_symbols.length ? item.sample_symbols.join(", ") : "数据集全部证券"}</td><td>{item.price_basis === "factor_adjusted" ? "close × adj_factor" : "导入的 close"}</td><td>{item.preprocessing.winsorize ? `MAD ${item.preprocessing.mad_scale}倍` : "不去极值"}<small>{item.preprocessing.standardize ? "Z-score标准化" : "不标准化"}</small></td><td>{item.code_version}</td></tr>)}</tbody></table></div></section>}
      {comparison && <section className="card comparison-table" style={{marginTop: 16}}><h2>数据来源性质</h2><p>来源类别只说明进入平台的方式，不证明市场数据真实性、使用许可或披露时点。</p>{comparison.items.map(item => <p key={item.run_id}>{item.experiment_name} · {comparisonSourceLabel(item.dataset_source_kind)}{item.dataset_source_kind === "bundled_demo" ? "；结果仅用于功能验收" : ""}</p>)}</section>}
    </> : view === "users" && isAdmin ? <>
      <header><div><p className="eyebrow">ACCESS CONTROL</p><h1>少量研究人员账号管理</h1><p>由管理员创建账号、分配角色并控制启停；平台不开放自行注册。</p></div></header>
      <form className="card user-create" onSubmit={createPlatformUser}><div><label>用户名</label><input name="username" required pattern="[A-Za-z][A-Za-z0-9_]+" minLength={3} placeholder="researcher2" /></div><div><label>显示名称</label><input name="display_name" required placeholder="研究员二号" /></div><div><label>初始密码</label><input name="password" type="password" required minLength={10} placeholder="至少10位" /></div><div><label>角色</label><select name="role" defaultValue="researcher"><option value="researcher">研究员</option><option value="viewer">只读用户</option><option value="admin">管理员</option></select></div><button disabled={loading}>创建账号</button></form>
      <section className="card user-table"><div className="user-row heading"><span>用户</span><span>角色</span><span>状态</span><span>创建时间</span><span>操作</span></div>{users.map(item => <div className="user-row" key={item.id}><span><b>{item.display_name}</b><small>{item.username}</small></span><span><select value={item.role} disabled={loading || item.id === user.id} onChange={event => updatePlatformUser(item.id, { role: event.target.value })}><option value="admin">管理员</option><option value="researcher">研究员</option><option value="viewer">只读用户</option></select></span><span><i className={item.is_active ? "active" : "disabled"}>{item.is_active ? "已启用" : "已停用"}</i></span><span><small>{formatTime(item.created_at)}</small></span><span><button disabled={loading || item.id === user.id} onClick={() => updatePlatformUser(item.id, { is_active: !item.is_active })}>{item.is_active ? "停用" : "启用"}</button></span></div>)}</section>
    </> : <>
      <header><div><p className="eyebrow">REPORT ARCHIVE</p><h1>把结构化结果变成可交付报告</h1><p>每份报告都绑定唯一Run，可在线预览、下载并打印为PDF。下载的是含数据披露的交付副本；原始归档保持不变。列表每 30 秒自动刷新，也可手动刷新。</p></div><div className="task-actions"><button className="secondary" onClick={() => loadReports().catch(error => setNotice(String(error)))}>刷新报告</button>{selectedReport && <button className="download" onClick={downloadReport}>下载披露版HTML</button>}</div></header>
      {isKnownSyntheticDemo(selectedReportDataset) && <div className="notice" role="note">当前报告对应内置合成演示数据，按工作日生成且含公告休市日行情；仅用于功能验收，不能作为真实市场证据。历史归档 HTML 按原始校验和提供，未被改写。</div>}
      {importedCsvProvenanceNotice(selectedReportDataset) && <div className="notice" role="note">当前报告对应的{importedCsvProvenanceNotice(selectedReportDataset)}归档 HTML 保持原始字节，下载交付副本会附加当前披露。</div>}
      {selectedReportDataset && !isKnownSyntheticDemo(selectedReportDataset) && (selectedReportDataset.quality_report.weekend_row_count ?? 0) > 0 && <div className="notice" role="alert">当前报告的数据版本含周末日期行情；请先核对源文件。历史归档 HTML 未改写。</div>}
      {reportCalendarNotice && <div className="notice" role="alert">{reportCalendarNotice}</div>}
      <section className="card task-filters"><label>检索报告<input type="search" value={reportQuery} onChange={event => setReportQuery(event.target.value)} placeholder="Run ID 或研究名称" /></label><span aria-live="polite">显示 {visibleReports.length}/{reports.length} 份报告</span></section>
      <section className="report-layout"><div className="card report-list">{visibleReports.map(item => <button key={item.run_id} className={selectedReport?.run_id === item.run_id ? "selected" : ""} onClick={() => setSelectedReportId(item.run_id)}><strong>{item.experiment_name}</strong><span>Run {item.run_id.slice(0, 8)} · 数据 {item.dataset_version} · 因子 {item.factor_version}</span><small>{formatTime(item.created_at)}</small></button>)}{reportListHint(reports.length, reportListLoading) && <div className="empty">{reportListHint(reports.length, reportListLoading)}</div>}{reports.length > 0 && visibleReports.length === 0 && <div className="empty">没有符合检索条件的报告。</div>}</div><div className="report-detail">{selectedReport && <section className="card report-identity" aria-label="当前报告身份"><div><span>完整 Run ID</span><code>{selectedReport.run_id}</code></div><div><span>归档 SHA-256</span><code>{selectedReport.checksum}</code></div><button className="secondary" onClick={openSelectedReportTask}>查看对应任务</button></section>}<div className="card report-preview">{selectedReport && visibleReportHtml ? <iframe title={selectedReport.experiment_name} srcDoc={visibleReportHtml} sandbox="allow-same-origin" /> : <div className="empty">{selectedReport ? "正在加载报告预览…" : reports.length > 0 && visibleReports.length === 0 ? "没有符合检索条件的报告可预览。" : "暂无可预览报告。"}</div>}</div></div></section>
    </>}<footer>研究结果仅用于课程研究，不构成投资建议。</footer></main></div>;
}

createRoot(document.getElementById("root")!).render(<App />);
