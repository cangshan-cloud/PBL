import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type CompositeResult = { method: string; weights: Record<string, number>; component_coverage: Record<string, number>; common_coverage: number; correlation_matrix: { left: string; right: string; correlation: number | null }[] };
type HistoricalAudit = Record<string, { totals: Record<string, number>; daily: { date: string; [key: string]: string | number }[]; unlabeled_signals: { date: string; symbol: string; factor: number; next_market_date: string | null; reason: string }[] }>;
type Result = { coverage: number; ic_mean: number | null; ic_std: number | null; rank_ic_mean: number | null; icir: number | null; ic_positive_ratio: number | null; long_short_mean: number | null; long_short_total_return: number | null; long_short_net_total_return: number | null; long_short_turnover: number | null; transaction_cost_bps: number; top_group_turnover: number | null; ic_series: { date: string; ic: number | null; rank_ic: number | null }[]; ic_histogram?: { lower: number; upper: number; count: number }[]; group_nav: { group: number; points: { date: string; nav: number }[] }[]; long_short_series: { date: string; return: number; nav: number; turnover: number; cost: number; net_return: number; net_nav: number }[]; group_returns: { group: number; mean_return: number }[]; composite?: CompositeResult; historical_audit?: HistoricalAudit };
type Task = { id: string; experiment_id?: string; experiment_name?: string; status: string; progress?: number; result?: Result; error_summary?: string; queued_at?: string; started_at?: string | null; finished_at?: string | null; cancellation_requested_at?: string | null; parameters?: Record<string, unknown>; dataset_version_id?: string; dataset_version?: string; factor_version_id?: string; factor_version?: string; code_version?: string };
type RunLog = { id: string; level: string; event: string; message: string; created_at: string };
type QualityReport = { valid?: boolean; dataset_kind?: string; bundle_id?: string; verified_files?: number; member_trading_days?: number; columns?: string[]; missing_counts?: Record<string, number>; completeness?: Record<string, number>; numeric_summary?: Record<string, { count: number; min: number; max: number; mean: number }> };
type Dataset = { id: string; dataset_key: string; name: string; version: string; start_date: string | null; end_date: string | null; row_count: number; symbol_count: number; checksum: string; source_filename: string; status: string; quality_report: QualityReport };
type DatasetPreview = { dataset_id: string; columns: string[]; rows: Record<string, string>[]; preview_count: number; total_rows: number; truncated: boolean };
type AdapterPreview = { report: { source_encoding: string; column_mapping: Record<string, string>; dropped_columns: string[]; converted_rows: number; warnings: string[]; validation: { row_count: number; symbol_count: number; start_date: string; end_date: string } }; preview: Record<string, string>[] };
type Report = { run_id: string; experiment_name: string; dataset_version: string; factor_version: string; created_at: string; checksum: string };
type User = { id: string; username: string; display_name: string; role: "admin" | "researcher" | "viewer"; is_active: boolean; created_at: string };
type Factor = { id: string; name: string; category: string; version: string; formula: string; description: string; required_columns: string[]; default_lookback: number | null; status: string };
type Dashboard = { scope: "personal" | "global"; datasets: { total: number; published: number; draft: number; latest_name: string | null }; factors: { builtin: number; composite_available: boolean }; tasks: { total: number; by_status: Record<string, number>; success_rate: number | null }; reports: { total: number }; recent_tasks: Task[]; recent_reports: Report[] };
type ComparisonItem = { run_id: string; experiment_name: string; factor: string; dataset_version: string; price_basis: "source_close" | "factor_adjusted"; groups: number; metrics: Record<string, number | null>; delta_from_baseline: Record<string, number | null>; ic_date_count: number; ic_start_date: string | null; ic_end_date: string | null; sample_symbols: string[]; preprocessing: { winsorize: boolean; standardize: boolean; mad_scale: number | null }; code_version: string };
type Comparison = { baseline_run_id: string; items: ComparisonItem[]; rankings: Record<string, string[]>; common_ic_date_count: number; comparable: boolean; warnings: string[] };
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

type NavLine = { label: string; color: string; values: number[] };
const groupColors = ["#277a5b", "#65a563", "#a5a944", "#d5a04b", "#b86e52", "#6d8bc3", "#805ca8", "#bc73aa", "#4e9ca3", "#707b7b"];

function NavChart({ eyebrow, title, lines, note, wide = false }: { eyebrow: string; title: string; lines: NavLine[]; note: string; wide?: boolean }) {
  const valid = lines.flatMap(line => line.values.filter(Number.isFinite));
  const length = Math.max(0, ...lines.map(line => line.values.length));
  let low = Math.min(1, ...valid); let high = Math.max(1, ...valid);
  if (low === high) { low -= 0.05; high += 0.05; }
  const padding = (high - low) * 0.08;
  low -= padding; high += padding;
  const y = (value: number) => 180 - (value - low) * 180 / (high - low);
  const x = (index: number) => length === 1 ? 300 : index * 600 / (length - 1);
  return <article className={`card line-chart${wide ? " group-nav" : ""}`}><p className="eyebrow">{eyebrow}</p><h2>{title}</h2>{valid.length ? <svg viewBox="0 0 600 180" preserveAspectRatio="none" role="img" aria-label={title}><line x1="0" y1={y(1)} x2="600" y2={y(1)} />{lines.map(line => line.values.length > 1 ? <polyline key={line.label} style={{ stroke: line.color }} points={line.values.map((value, index) => `${x(index)},${y(value)}`).join(" ")} /> : line.values.length === 1 ? <circle key={line.label} cx={x(0)} cy={y(line.values[0])} r="3" style={{ fill: line.color }} /> : null)}</svg> : <div className="empty">暂无净值序列。</div>}<div className="chart-legend">{lines.map(line => <span key={line.label}><i style={{ background: line.color }} />{line.label} · {line.values.length ? number(line.values.at(-1)) : "—"}</span>)}</div><small>{note}</small></article>;
}

function icHistogram(values: (number | null)[]) {
  const counts = Array(10).fill(0) as number[];
  values.forEach(value => {
    if (value != null && Number.isFinite(value)) counts[Math.min(9, Math.max(0, Math.floor((value + 1) * 5 + 1e-12)))] += 1;
  });
  return counts.map((count, index) => ({ lower: Number((-1 + index * 0.2).toFixed(1)), upper: Number((-0.8 + index * 0.2).toFixed(1)), count }));
}

function IcSeriesChart({ series }: { series: Result["ic_series"] }) {
  const values = series.map(item => item.ic);
  const valid = values.filter((value): value is number => value != null && Number.isFinite(value));
  const low = Math.min(0, ...valid); const high = Math.max(0, ...valid);
  const span = high - low || 1; const padding = span * 0.08;
  const y = (value: number) => 180 - (value - (low - padding)) * 180 / (span + padding * 2);
  const segments: { x: number; y: number }[][] = [];
  let current: { x: number; y: number }[] = [];
  values.forEach((value, index) => {
    if (value == null || !Number.isFinite(value)) {
      if (current.length) segments.push(current);
      current = [];
    } else current.push({ x: series.length === 1 ? 300 : index * 600 / (series.length - 1), y: y(value) });
  });
  if (current.length) segments.push(current);
  return <article className="card line-chart"><p className="eyebrow">IC SERIES</p><h2>每日 IC</h2>{valid.length ? <svg viewBox="0 0 600 180" preserveAspectRatio="none" role="img" aria-label="每日 IC，空值处断开"><line x1="0" y1={y(0)} x2="600" y2={y(0)} />{segments.map((segment, index) => segment.length > 1 ? <polyline key={index} points={segment.map(point => `${point.x},${point.y}`).join(" ")} /> : <circle key={index} cx={segment[0].x} cy={segment[0].y} r="3" />)}</svg> : <div className="empty">没有可计算的 IC。</div>}<small>{valid.length} 个有效截面；{values.length - valid.length} 个空值不按零填补</small></article>;
}

function IcDistribution({ result }: { result: Result }) {
  const histogram = result.ic_histogram ?? icHistogram(result.ic_series.map(item => item.ic));
  const maximum = Math.max(1, ...histogram.map(item => item.count));
  const total = histogram.reduce((sum, item) => sum + item.count, 0);
  return <article className="card ic-distribution"><p className="eyebrow">IC DISTRIBUTION</p><h2>IC 分布</h2><div className="bars">{histogram.map(item => <div className="bar-row" key={item.lower}><span>{item.lower.toFixed(1)}～{item.upper.toFixed(1)}</span><div><i style={{ width: `${item.count / maximum * 100}%` }} /></div><strong>{item.count}</strong></div>)}</div><small>固定 0.2 宽度分箱 · {total} 个有效交易日，空值不计入</small></article>;
}

function App() {
  const [user, setUser] = React.useState<User | null>(null);
  const [authChecked, setAuthChecked] = React.useState(false);
  const [view, setView] = React.useState<"dashboard" | "research" | "factors" | "datasets" | "tasks" | "comparisons" | "reports" | "users">("dashboard");
  const [dashboard, setDashboard] = React.useState<Dashboard | null>(null);
  const [users, setUsers] = React.useState<User[]>([]);
  const [task, setTask] = React.useState<Task | null>(null);
  const [tasks, setTasks] = React.useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = React.useState("");
  const [taskLogs, setTaskLogs] = React.useState<RunLog[]>([]);
  const [taskConclusion, setTaskConclusion] = React.useState<Conclusion | null>(null);
  const [comparisonRunIds, setComparisonRunIds] = React.useState<string[]>([]);
  const [comparison, setComparison] = React.useState<Comparison | null>(null);
  const [reports, setReports] = React.useState<Report[]>([]);
  const [selectedReportId, setSelectedReportId] = React.useState("");
  const [reportHtml, setReportHtml] = React.useState("");
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
  const [sampleSymbols, setSampleSymbols] = React.useState("");
  const [datasetPreview, setDatasetPreview] = React.useState<DatasetPreview | null>(null);
  const [adapterPreview, setAdapterPreview] = React.useState<AdapterPreview | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [notice, setNotice] = React.useState("");
  const published = datasets.filter(item => item.status === "published");
  const isHistoricalDataset = (item: Dataset) => item.quality_report.dataset_kind === "hs300_bundle_v1";
  const eligibleDatasets = published.filter(item => researchMode === "historical" ? isHistoricalDataset(item) : !isHistoricalDataset(item));
  const selected = eligibleDatasets.find(item => item.id === selectedDataset) ?? eligibleDatasets[0];
  const selectedFactor = factors.find(item => item.id === selectedFactorKey) ?? factors[0];
  const selectedTask = tasks.find(item => item.id === selectedTaskId) ?? tasks[0];
  const selectedReport = reports.find(item => item.run_id === selectedReportId) ?? reports[0];

  const loadDatasets = React.useCallback(async () => {
    const response = await apiFetch("/datasets");
    if (!response.ok) throw new Error("数据版本加载失败");
    const value = await response.json() as Dataset[];
    setDatasets(value);
    setSelectedDataset(current => current || value.find(item => item.status === "published")?.id || "");
  }, []);

  const loadFactors = React.useCallback(async () => {
    const response = await apiFetch("/factors");
    if (!response.ok) throw new Error("因子库加载失败");
    setFactors(await response.json() as Factor[]);
  }, []);

  const loadDashboard = React.useCallback(async () => {
    const response = await apiFetch("/dashboard");
    if (!response.ok) throw new Error("项目总览加载失败");
    setDashboard(await response.json() as Dashboard);
  }, []);

  const loadUsers = React.useCallback(async () => {
    const response = await apiFetch("/users");
    if (!response.ok) throw new Error("用户列表加载失败");
    setUsers(await response.json() as User[]);
  }, []);

  const loadTasks = React.useCallback(async () => {
    const response = await apiFetch("/research/tasks");
    if (!response.ok) throw new Error("任务列表加载失败");
    const value = await response.json() as Task[];
    setTasks(value);
    setSelectedTaskId(current => value.some(item => item.id === current) ? current : value[0]?.id || "");
  }, []);

  const loadReports = React.useCallback(async () => {
    const response = await apiFetch("/reports");
    if (!response.ok) throw new Error("报告列表加载失败");
    const value = await response.json() as Report[];
    setReports(value);
    setSelectedReportId(current => value.some(item => item.run_id === current) ? current : value[0]?.run_id || "");
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
    loadTasks().catch(error => setNotice(String(error)));
    const timer = window.setInterval(() => loadTasks().catch(() => undefined), 2000);
    return () => window.clearInterval(timer);
  }, [user, view, loadTasks]);
  React.useEffect(() => { if (user && view === "comparisons") loadTasks().catch(error => setNotice(String(error))); }, [user, view, loadTasks]);
  React.useEffect(() => { if (user && view === "reports") loadReports().catch(error => setNotice(String(error))); }, [user, view, loadReports]);
  React.useEffect(() => { if (user?.role === "admin" && view === "users") loadUsers().catch(error => setNotice(String(error))); }, [user, view, loadUsers]);
  React.useEffect(() => {
    if (!user || view !== "reports" || !selectedReport) { setReportHtml(""); return; }
    apiFetch(`/reports/${selectedReport.run_id}/html`).then(async response => {
      if (!response.ok) throw new Error("报告预览加载失败");
      setReportHtml(await response.text());
    }).catch(error => setNotice(String(error)));
  }, [user, view, selectedReport]);
  React.useEffect(() => {
    if (!user || view !== "tasks" || !selectedTask) { setTaskLogs([]); return; }
    apiFetch(`/research/tasks/${selectedTask.id}/logs`).then(async response => {
      if (!response.ok) throw new Error("任务日志加载失败");
      setTaskLogs(await response.json() as RunLog[]);
    }).catch(error => setNotice(String(error)));
  }, [user, view, selectedTask?.id, selectedTask?.status]);
  React.useEffect(() => {
    if (!user || view !== "tasks" || selectedTask?.status !== "success") { setTaskConclusion(null); return; }
    apiFetch(`/research/tasks/${selectedTask.id}/conclusion`).then(async response => {
      if (!response.ok) throw new Error("研究结论加载失败");
      setTaskConclusion(await response.json() as Conclusion);
    }).catch(error => setNotice(String(error)));
  }, [user, view, selectedTask?.id, selectedTask?.status]);

  async function runResearch() {
    if (!selected) { setNotice(researchMode === "historical" ? "请先注册并发布历史沪深300数据包" : "请先导入并发布一个CSV数据版本"); setView("datasets"); return; }
    setLoading(true); setNotice("");
    try {
      const symbols = sampleSymbols.split(/[\s,;]+/).map(value => value.trim()).filter(Boolean);
      const sample = { start_date: sampleStart || null, end_date: sampleEnd || null, symbols: symbols.length ? symbols : null };
      const parameters: Record<string, unknown> = researchMode === "historical"
        ? { dataset_version_id: selected.id, groups }
        : researchMode === "composite"
        ? { factors: compositeFactors, dataset_version_id: selected.id, groups, winsorize, standardize, mad_scale: 3, transaction_cost_bps: transactionCostBps, price_basis: priceBasis, ...sample }
        : { factor: selectedFactor.id, dataset_version_id: selected.id, groups, winsorize, standardize, mad_scale: 3, transaction_cost_bps: transactionCostBps, price_basis: priceBasis, ...sample };
      if (researchMode === "single" && selectedFactor.default_lookback !== null) parameters.lookback = lookback;
      const endpoint = researchMode === "historical" ? "/research/historical-tasks" : researchMode === "composite" ? "/research/composite-tasks" : "/research/tasks";
      const response = await apiFetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(parameters) });
      const payload = await response.json();
      let value = payload as Task;
      if (!response.ok) throw new Error(errorMessage(payload, "任务提交失败"));
      setTask(value);
      while (value.status === "pending" || value.status === "running") {
        await new Promise(resolve => window.setTimeout(resolve, 500));
        const poll = await apiFetch(`/research/tasks/${value.id}`);
        const pollPayload = await poll.json();
        if (!poll.ok) throw new Error(errorMessage(pollPayload, "任务状态查询失败"));
        value = pollPayload as Task; setTask(value);
      }
    } catch (error) { setTask({ id: "local-error", status: "failed", error_summary: String(error) }); }
    finally { setLoading(false); loadTasks().catch(() => undefined); loadReports().catch(() => undefined); loadDashboard().catch(() => undefined); }
  }

  async function uploadDataset(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setNotice("");
    const form = event.currentTarget;
    try {
      const response = await apiFetch("/datasets/import", { method: "POST", body: new FormData(form) });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "数据导入失败"));
      setNotice(`已导入 ${payload.name}，请检查后发布`); form.reset(); setAdapterPreview(null); await loadDatasets();
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
    const body = new FormData(); body.append("file", file.files[0]);
    setLoading(true); setNotice("");
    try {
      const response = await apiFetch("/datasets/adapt/preview", { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "字段适配预览失败"));
      setAdapterPreview(payload as AdapterPreview);
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
    currentToken = "";
    window.localStorage.removeItem("factorlab_token");
    setUser(null);
    setView("dashboard");
    setDashboard(null);
    setUsers([]);
    setDatasets([]);
    setFactors([]);
    setTask(null);
    setTasks([]);
    setSelectedTaskId("");
    setTaskLogs([]);
    setTaskConclusion(null);
    setComparisonRunIds([]);
    setComparison(null);
    setReports([]);
    setSelectedReportId("");
    setReportHtml("");
    setDatasetPreview(null);
    setAdapterPreview(null);
    setNotice("");
  }

  async function downloadReport() {
    if (!selectedReport) return;
    const response = await apiFetch(`/reports/${selectedReport.run_id}/download`);
    if (!response.ok) { setNotice("报告下载失败"); return; }
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `factor-report-${selectedReport.run_id.slice(0, 8)}.html`; anchor.click(); URL.revokeObjectURL(url);
  }

  async function downloadReproducibilityBundle() {
    if (!selectedTask) return;
    setNotice("");
    try {
      const response = await apiFetch(`/research/tasks/${selectedTask.id}/reproducibility.json`);
      if (!response.ok) { const payload = await response.json(); throw new Error(errorMessage(payload, "复现包下载失败")); }
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `factor-run-${selectedTask.id.slice(0, 8)}.json`; anchor.click(); URL.revokeObjectURL(url);
    } catch (error) { setNotice(String(error)); }
  }

  async function downloadHistoricalAudit(table: "daily" | "unlabeled") {
    if (!selectedTask) return;
    setNotice("");
    try {
      const response = await apiFetch(`/research/tasks/${selectedTask.id}/historical-audit/${table}.csv`);
      if (!response.ok) { const payload = await response.json(); throw new Error(errorMessage(payload, "审计 CSV 下载失败")); }
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `historical-audit-${table}-${selectedTask.id.slice(0, 8)}.csv`; anchor.click(); URL.revokeObjectURL(url);
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
    setComparison(null);
    setComparisonRunIds(current => current.includes(id) ? current.filter(item => item !== id) : current.length < 6 ? [...current, id] : current);
  }

  async function runComparison() {
    if (comparisonRunIds.length < 2) return;
    setLoading(true); setNotice("");
    try {
      const response = await apiFetch("/research/comparisons", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_ids: comparisonRunIds }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload, "实验对比失败"));
      setComparison(payload as Comparison);
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
  }

  async function downloadComparison(format: "csv" | "html") {
    if (!comparison || comparisonRunIds.length < 2) return;
    setLoading(true); setNotice("");
    try {
      const response = await apiFetch(`/research/comparisons/export.${format}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_ids: comparisonRunIds }) });
      if (!response.ok) { const payload = await response.json(); throw new Error(errorMessage(payload, "对比文件导出失败")); }
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `factorlab-comparison.${format}`; anchor.click(); URL.revokeObjectURL(url);
    } catch (error) { setNotice(String(error)); }
    finally { setLoading(false); }
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
  return <div className="shell"><aside><div className="brand"><span>FL</span><strong>FactorLab</strong></div><nav><button className={view === "dashboard" ? "active" : ""} onClick={() => { setView("dashboard"); loadDashboard().catch(() => undefined); }}>项目总览</button><button className={view === "research" ? "active" : ""} onClick={() => setView("research")}>研究工作台</button><button className={view === "datasets" ? "active" : ""} onClick={() => setView("datasets")}>数据集</button><button className={view === "factors" ? "active" : ""} onClick={() => setView("factors")}>因子库</button><button className={view === "tasks" ? "active" : ""} onClick={() => setView("tasks")}>任务中心</button><button className={view === "comparisons" ? "active" : ""} onClick={() => setView("comparisons")}>实验对比</button><button className={view === "reports" ? "active" : ""} onClick={() => setView("reports")}>报告中心</button>{isAdmin && <button className={view === "users" ? "active" : ""} onClick={() => setView("users")}>用户管理</button>}</nav><div className="account"><strong>{user.display_name}</strong><span>{user.role}</span><button onClick={logout}>退出登录</button></div><p className="scope">课程验收版 · 沪深 A 股日频</p></aside>
    <main>{notice && <div className="notice">{notice}</div>}{view === "dashboard" ? <>
      <header><div><p className="eyebrow">PROJECT OVERVIEW · {dashboard?.scope === "personal" ? "PERSONAL" : "GLOBAL"}</p><h1>研究平台运行概览</h1><p>{dashboard?.scope === "personal" ? "展示共享研究资源和你创建的任务与报告。" : "展示平台共享资源及全部研究活动。"}</p></div><button onClick={() => setView("research")} disabled={!canResearch}>{canResearch ? "新建研究" : "只读访问"}</button></header>
      <section className="overview-metrics"><article className="card"><label>已发布数据</label><b>{dashboard?.datasets.published ?? "—"}</b><small>草稿 {dashboard?.datasets.draft ?? 0} · 共 {dashboard?.datasets.total ?? 0} 个版本</small></article><article className="card"><label>内置因子</label><b>{dashboard?.factors.builtin ?? "—"}</b><small>支持等权多因子合成</small></article><article className="card"><label>研究任务</label><b>{dashboard?.tasks.total ?? "—"}</b><small>成功率 {number(dashboard?.tasks.success_rate, true)}</small></article><article className="card"><label>研究报告</label><b>{dashboard?.reports.total ?? "—"}</b><small>成功任务自动归档</small></article></section>
      <section className="overview-grid"><article className="card status-overview"><div className="section-title"><div><p className="eyebrow">TASK HEALTH</p><h2>任务状态分布</h2></div><button onClick={() => setView("tasks")}>查看全部</button></div>{["success","running","pending","failed","cancelled"].map(status => { const count = dashboard?.tasks.by_status[status] ?? 0; const total = dashboard?.tasks.total || 1; return <div className="status-row" key={status}><span>{statusLabel(status)}</span><div><i className={status} style={{width: `${count / total * 100}%`}} /></div><b>{count}</b></div>; })}</article><article className="card recent-activity"><div className="section-title"><div><p className="eyebrow">RECENT RUNS</p><h2>近期研究活动</h2></div></div>{dashboard?.recent_tasks.map(item => <button key={item.id} onClick={() => { setSelectedTaskId(item.id); setView("tasks"); }}><span className={`status ${item.status}`}>{statusLabel(item.status)}</span><b>{item.experiment_name}</b><small>{formatTime(item.queued_at)}</small></button>)}{!dashboard?.recent_tasks.length && <div className="empty">尚无研究任务，从研究工作台开始第一次运行。</div>}</article></section>
      <section className="card platform-scope"><div><p className="eyebrow">CURRENT SCOPE</p><h2>沪深 A 股 · 日频 · 私有部署</h2></div><span>最新数据：{dashboard?.datasets.latest_name ?? "暂无"}</span><span>研究结果仅用于课程研究，不构成投资建议</span></section>
    </> : view === "research" ? <>
      <header><div><p className="eyebrow">RESEARCH WORKSPACE</p><h1>把因子想法变成可复现的证据</h1><p>固定数据版本、因子口径与检验参数，一次运行保留完整研究轨迹。</p></div><button onClick={runResearch} disabled={loading || !canResearch || !selected || (researchMode === "single" ? !selectedFactor : researchMode === "composite" ? compositeFactors.length < 2 : false)}>{!canResearch ? "只读模式" : loading ? "正在运行…" : "运行研究"}</button></header>
      <div className="mode-switch"><button className={researchMode === "single" ? "active" : ""} onClick={() => setResearchMode("single")}>单因子检验</button><button className={researchMode === "composite" ? "active" : ""} onClick={() => setResearchMode("composite")}>等权多因子</button><button className={researchMode === "historical" ? "active" : ""} onClick={() => setResearchMode("historical")}>2024 沪深300历史研究</button></div>
      {researchMode === "historical" ? <><section className="config card"><div><label htmlFor="historical-dataset">历史数据包</label><select id="historical-dataset" value={selected?.id ?? ""} onChange={event => setSelectedDataset(event.target.value)}>{eligibleDatasets.map(item => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}</select></div><div><label>因子组合</label><strong>动量20日 · 反转5日 · 波动率20日 · 换手率20日</strong></div><div><label>研究期间</label><strong>2024 年；按日历史成分</strong></div><div><label htmlFor="groups">分组数量</label><input id="groups" type="number" min="2" max="10" value={groups} onChange={event => setGroups(Number(event.target.value))} /></div></section><div className="notice">固定等权、原始数据包价格、MAD 去极值、Z-score 与单边 10 bps 成本假设。结果只是条件研究检验，不代表实际可成交回测。{!selected && " 尚无已发布历史包，请先到数据集页面注册并发布。"}</div></> : <>
      <section className="price-basis card"><label htmlFor="price-basis">价格口径</label><select id="price-basis" value={priceBasis} onChange={event => setPriceBasis(event.target.value as "source_close" | "factor_adjusted")}><option value="source_close">使用导入的 close</option><option value="factor_adjusted">close × adj_factor</option></select><small>若导入价格已经复权，请使用原始导入价格；选择因子调整时，每行必须有正数 adj_factor。</small></section>
      <section className="config card"><div><label htmlFor="dataset">数据版本</label><select id="dataset" value={selected?.id ?? ""} onChange={event => setSelectedDataset(event.target.value)}>{eligibleDatasets.map(item => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}</select></div><div><label htmlFor="factor">研究因子</label>{researchMode === "single" ? <select id="factor" value={selectedFactor?.id ?? ""} onChange={event => { const next = factors.find(item => item.id === event.target.value); setSelectedFactorKey(event.target.value); if (next?.default_lookback) setLookback(next.default_lookback); }}>{factors.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select> : <strong>{compositeFactors.length} 个因子等权合成</strong>}</div><div><label htmlFor="lookback">回看窗口</label>{researchMode === "single" ? selectedFactor?.default_lookback !== null ? <input id="lookback" type="number" min="2" max="120" value={lookback} onChange={event => setLookback(Number(event.target.value))} /> : <strong>当日截面</strong> : <strong>使用各因子默认窗口</strong>}</div><div><label htmlFor="groups">分组数量</label><input id="groups" type="number" min="2" max="10" value={groups} onChange={event => setGroups(Number(event.target.value))} /><small>t 日因子 → t+1 收益</small></div></section>
      <section className="sample-config card"><div><label htmlFor="sample-start">因子起始日</label><input id="sample-start" type="date" min={selected?.start_date ?? undefined} max={sampleEnd || selected?.end_date || undefined} value={sampleStart} onChange={event => setSampleStart(event.target.value)} /></div><div><label htmlFor="sample-end">因子结束日</label><input id="sample-end" type="date" min={sampleStart || selected?.start_date || undefined} max={selected?.end_date ?? undefined} value={sampleEnd} onChange={event => setSampleEnd(event.target.value)} /></div><div><label htmlFor="sample-symbols">证券样本（可选）</label><input id="sample-symbols" value={sampleSymbols} onChange={event => setSampleSymbols(event.target.value)} placeholder="留空表示全部；多个代码用逗号分隔" /></div><small>因子计算会读取起始日前所需历史，但结果只保留所选日期。</small></section>
      {researchMode === "composite" && <section className="factor-picker card"><div><strong>选择成分因子</strong><small>至少2个；先分别进行截面预处理，再取共同样本等权合成。</small></div>{factors.map(item => <label key={item.id}><input type="checkbox" checked={compositeFactors.includes(item.id)} onChange={() => toggleCompositeFactor(item.id)} /><span>{item.name}</span><small>{item.default_lookback ? `${item.default_lookback}日` : "当日"}</small></label>)}</section>}
      <section className="preprocess card"><strong>截面预处理</strong><label><input type="checkbox" checked={winsorize} onChange={event => setWinsorize(event.target.checked)} /> MAD 3倍去极值</label><label><input type="checkbox" checked={standardize} onChange={event => setStandardize(event.target.checked)} /> Z-score标准化</label><label className="cost-input">单边成本 <input type="number" min="0" max="100" step="1" value={transactionCostBps} onChange={event => setTransactionCostBps(Number(event.target.value))} /> bps</label><small>按多空两边实际成员换手扣减固定成本。</small></section></>}
      <section className="metrics"><article className="card"><label>有效观测</label><b>{task?.result?.coverage ?? "—"}</b><small>股票 × 交易日</small></article><article className="card"><label>IC 均值</label><b>{number(task?.result?.ic_mean)}</b><small>Pearson 相关</small></article><article className="card"><label>Rank IC</label><b>{number(task?.result?.rank_ic_mean)}</b><small>Spearman 相关</small></article><article className="card"><label>ICIR</label><b>{number(task?.result?.icir)}</b><small>未年化</small></article><article className="card"><label>IC为正比例</label><b>{number(task?.result?.ic_positive_ratio, true)}</b><small>方向稳定性</small></article><article className="card"><label>毛多空累计收益</label><b>{number(task?.result?.long_short_total_return, true)}</b><small>Q5 − Q1</small></article><article className="card"><label>成本后多空收益</label><b>{number(task?.result?.long_short_net_total_return, true)}</b><small>单边 {task?.result?.transaction_cost_bps ?? transactionCostBps} bps</small></article><article className="card"><label>多空双边换手</label><b>{number(task?.result?.long_short_turnover, true)}</b><small>包含首次建仓</small></article></section>
      <section className="card result"><div className="section-title"><div><p className="eyebrow">QUANTILE RETURN</p><h2>分组平均下一日收益</h2></div><span className={`status ${task?.status ?? "idle"}`}>{task?.status === "success" ? "计算完成" : task?.status === "failed" ? "运行失败" : task ? `${task.progress ?? 0}%` : "等待运行"}</span></div>{task?.error_summary && <p className="error">{task.error_summary}</p>}<div className="bars">{(task?.result?.group_returns ?? [1,2,3,4,5].map(group => ({group, mean_return: 0}))).map(item => <div className="bar-row" key={item.group}><span>Q{item.group}</span><div><i style={{width: `${task?.result ? Math.min(100, Math.abs(item.mean_return) * 4000 + 8) : 8}%`}} /></div><strong>{number(item.mean_return, true)}</strong></div>)}</div></section>
      {task?.result && <section className="chart-grid"><IcSeriesChart series={task.result.ic_series} /><NavChart eyebrow="LONG SHORT NAV" title="多空组合净值" lines={[{ label: "毛净值", color: "#277a5b", values: task.result.long_short_series.map(item => item.nav) }, { label: "成本后净值", color: "#d69043", values: task.result.long_short_series.map(item => item.net_nav) }]} note={`初值 1；成本后净值扣除 ${task.result.transaction_cost_bps} bps 单边成本`} /><IcDistribution result={task.result} /><NavChart eyebrow="QUANTILE NAV" title="各组净值" lines={(task.result.group_nav ?? []).map(item => ({ label: `Q${item.group}`, color: groupColors[(item.group - 1) % groupColors.length], values: item.points.map(point => point.nav) }))} note="各组等权日收益连乘，初值 1；与分组平均收益使用同一结果数据" wide /></section>}
      {task?.result?.composite && <section className="card composite-result"><div className="section-title"><div><p className="eyebrow">COMPOSITE DIAGNOSTICS</p><h2>多因子合成诊断</h2></div><strong>共同样本 {task.result.composite.common_coverage}</strong></div><div className="weight-list">{Object.entries(task.result.composite.weights).map(([key, value]) => <span key={key}><b>{factorName(key)}</b>{number(value, true)}<small>原始覆盖 {task.result!.composite!.component_coverage[key]}</small></span>)}</div><h3>因子相关矩阵</h3><div className="correlation-table">{task.result.composite.correlation_matrix.map(item => <span key={`${item.left}-${item.right}`}><b>{factorName(item.left)} × {factorName(item.right)}</b>{number(item.correlation)}</span>)}</div></section>}
      {task?.result?.historical_audit && <section className="card historical-audit"><div className="section-title"><div><p className="eyebrow">HISTORICAL AUDIT</p><h2>历史股票池与标签审计</h2></div><strong>2024 沪深300</strong></div><p>逐日按历史成分及交易状态筛选；下一日收益缺失不填零、不跳至复牌日。以下是研究样本检验，并非真实可成交收益。</p><div className="preview-scroll"><table><thead><tr><th>因子</th><th>候选</th><th>有效信号</th><th>有效收益</th><th>窗口无效</th><th>次日不可用</th></tr></thead><tbody>{Object.entries(task.result.historical_audit).map(([key, item]) => <tr key={key}><td>{factorName(key)}</td><td>{item.totals.candidate_count ?? 0}</td><td>{item.totals.factor_signal ?? 0}</td><td>{item.totals.valid_return ?? 0}</td><td>{item.totals.invalid_contiguous_window ?? 0}</td><td>{item.unlabeled_signals.length}</td></tr>)}</tbody></table></div><div className="task-actions"><button onClick={() => downloadHistoricalAudit("daily")}>下载逐日审计 CSV</button><button onClick={() => downloadHistoricalAudit("unlabeled")}>下载无标签信号 CSV</button></div><small>完整逐日计数及无标签信号的证券、日期、因子值和原因也保存在任务结果与复现包中。</small></section>}
    </> : view === "factors" ? <>
      <header><div><p className="eyebrow">FACTOR CATALOG</p><h1>六个内置因子，统一口径与版本</h1><p>每个因子明确公式、字段依赖和默认窗口，研究任务会固定因子版本。</p></div></header>
      <section className="factor-grid">{factors.map(item => <article className={`card factor-card ${selectedFactor?.id === item.id ? "selected" : ""}`} key={item.id} onClick={() => { setSelectedFactorKey(item.id); if (item.default_lookback) setLookback(item.default_lookback); }}><div className="section-title"><span className="factor-category">{item.category}</span><small>v{item.version}</small></div><h2>{item.name}</h2><p>{item.description}</p><code>{item.formula}</code><div><label>所需字段</label><span>{item.required_columns.join(" · ")}</span></div><button onClick={() => { setResearchMode("single"); setView("research"); }}>用于研究</button></article>)}</section>
    </> : view === "datasets" ? <>
      <header><div><p className="eyebrow">DATA GOVERNANCE</p><h1>每一次研究，从确定的数据版本开始</h1><p>导入日行情 CSV 或注册封存的历史数据包，核验后发布为研究输入。</p></div></header>
      {isAdmin ? <><form className="card upload adapted-upload" onSubmit={uploadDataset}><div><label htmlFor="dataset_key">数据集标识</label><input id="dataset_key" name="dataset_key" required pattern="[a-z][a-z0-9_]{2,49}" placeholder="例如 csi300_daily" /></div><div><label htmlFor="name">显示名称</label><input id="name" name="name" required placeholder="例如 沪深300日行情" /></div><div><label htmlFor="file">CSV文件</label><input id="file" name="file" type="file" accept=".csv,text/csv" required onChange={() => setAdapterPreview(null)} /></div><label className="adapter-toggle"><input name="normalize_cn_csv" type="checkbox" value="true" /> 自动适配常见A股字段</label><button type="button" className="secondary" onClick={previewAdapter} disabled={loading}>适配预览</button><button disabled={loading}>{loading ? "处理中…" : "导入并检查"}</button></form>{adapterPreview && <section className="card adapter-preview"><div className="section-title"><div><p className="eyebrow">CN CSV ADAPTER</p><h2>标准化预览</h2></div><span>{adapterPreview.report.converted_rows} 行 · {adapterPreview.report.source_encoding}</span></div><div className="mapping-list">{Object.entries(adapterPreview.report.column_mapping).map(([source, target]) => <span key={source}><b>{source}</b> → {target}</span>)}</div>{adapterPreview.report.dropped_columns.length > 0 && <p>未导入字段：{adapterPreview.report.dropped_columns.join("、")}</p>}<div className="preview-scroll"><table><thead><tr>{Object.keys(adapterPreview.preview[0] ?? {}).map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{adapterPreview.preview.map((row, index) => <tr key={index}>{Object.keys(row).map(column => <td key={column}>{row[column]}</td>)}</tr>)}</tbody></table></div><ul>{adapterPreview.report.warnings.map(item => <li key={item}>{item}</li>)}</ul></section>}</> : <div className="notice">当前角色可以查看数据版本，但只有管理员可以导入和发布。</div>}
      {isAdmin && <form className="card bundle-registration" onSubmit={registerHistoricalBundle}><div><p className="eyebrow">SEALED HISTORICAL BUNDLE</p><h2>注册本机历史数据包</h2><small>先将私有包放在 DATA_ROOT 同级的 real/bundles 目录；输入包 ID 注册草稿，核对后再发布。</small></div><label htmlFor="bundle-id">包 ID<input id="bundle-id" value={bundleId} onChange={event => setBundleId(event.target.value)} placeholder="hs300_2024_…" pattern="hs300_2024_[0-9a-f]{16}" required /></label><button disabled={loading}>{loading ? "校验中…" : "注册历史包"}</button></form>}
      <section className="dataset-list">{datasets.map(item => <article className="card dataset" key={item.id}><div className="section-title"><div><p className="eyebrow">{item.dataset_key}</p><h2>{item.name}</h2></div><span className={`status ${item.status === "published" ? "success" : "idle"}`}>{item.status === "published" ? "已发布" : "草稿"}</span></div><div className="dataset-stats"><span><b>{item.row_count}</b> 行</span><span><b>{item.symbol_count}</b> 只证券</span><span><b>{item.start_date ?? "—"}</b> 起始</span><span><b>{item.end_date ?? "—"}</b> 结束</span></div><div className="quality-summary">{isHistoricalDataset(item) ? <><span><b>{item.quality_report.verified_files ?? "—"}</b>已校验文件</span><span><b>{item.quality_report.member_trading_days ?? "—"}</b>历史成员日</span><span><b>整包摘要</b>非逐字段质量检查</span></> : <><span><b>{item.quality_report.columns?.length ?? 3}</b>字段</span><span><b>{Object.values(item.quality_report.missing_counts ?? {}).reduce((sum, value) => sum + value, 0)}</b>缺失单元格</span><span><b>{item.quality_report.valid === false ? "异常" : "通过"}</b>质量检查</span></>}</div><p className="checksum">SHA-256 · {item.checksum}</p><div className="dataset-actions"><span>{item.source_filename} · 版本 {item.version}</span><div><button className="secondary" onClick={() => toggleDatasetPreview(item.id)} disabled={loading}>{datasetPreview?.dataset_id === item.id ? "收起详情" : isHistoricalDataset(item) ? "查看清单摘要" : "质量与预览"}</button>{isAdmin && item.status === "draft" && <button onClick={() => publishDataset(item.id)} disabled={loading}>确认发布</button>}</div></div>{datasetPreview?.dataset_id === item.id && <div className="dataset-preview">{isHistoricalDataset(item) ? <><h3>封存包清单摘要</h3><p>展示包身份与文件计数，不代表对行情字段完整率的逐项检查。</p></> : <><h3>字段完整率</h3><div className="field-quality">{(item.quality_report.columns ?? datasetPreview.columns).map(column => <span key={column}><b>{column}</b><i>{number(item.quality_report.completeness?.[column] ?? 1, true)}</i><small>缺失 {item.quality_report.missing_counts?.[column] ?? 0}</small></span>)}</div>{Object.keys(item.quality_report.numeric_summary ?? {}).length > 0 && <><h3>数值字段范围</h3><div className="numeric-quality">{Object.entries(item.quality_report.numeric_summary ?? {}).map(([column, stats]) => <span key={column}><b>{column}</b><small>最小 {number(stats.min)}</small><small>均值 {number(stats.mean)}</small><small>最大 {number(stats.max)}</small></span>)}</div></>}</>}<h3>{isHistoricalDataset(item) ? "清单项目" : `前 ${datasetPreview.preview_count} 行预览`}</h3><div className="preview-scroll"><table><thead><tr>{datasetPreview.columns.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{datasetPreview.rows.map((row, index) => <tr key={index}>{datasetPreview.columns.map(column => <td key={column}>{row[column] || <em>空</em>}</td>)}</tr>)}</tbody></table></div>{datasetPreview.truncated && <small>仅展示前 {datasetPreview.preview_count} 行，共 {datasetPreview.total_rows} 行。</small>}</div>}</article>)}{!datasets.length && <div className="empty card">尚无数据版本。</div>}</section>
    </> : view === "tasks" ? <>
      <header><div><p className="eyebrow">RUN REGISTRY</p><h1>每次运行都有状态，也有来路</h1><p>查看任务进度、失败原因、版本绑定与不可变研究结果。</p></div><button onClick={() => loadTasks()} disabled={loading}>刷新任务</button></header>
      <section className="task-layout">
        <div className="card task-list">{tasks.map(item => <button key={item.id} className={selectedTask?.id === item.id ? "selected" : ""} onClick={() => setSelectedTaskId(item.id)}><span className={`status ${item.status}`}>{statusLabel(item.status)}</span><strong>{item.experiment_name ?? "研究任务"}</strong><small>{formatTime(item.queued_at)}</small><i><b style={{width: `${item.progress ?? 0}%`}} /></i></button>)}{!tasks.length && <div className="empty">尚无研究任务。</div>}</div>
        <div className="card task-detail">{selectedTask ? <><div className="section-title"><div><p className="eyebrow">RUN · {selectedTask.id.slice(0, 8)}</p><h2>{selectedTask.experiment_name}</h2></div><div className="task-actions"><span className={`status ${selectedTask.status}`}>{statusLabel(selectedTask.status)}</span><button onClick={downloadReproducibilityBundle}>下载复现包</button>{canResearch && (selectedTask.status === "pending" || selectedTask.status === "running") && <button onClick={() => taskAction("cancel")} disabled={loading || Boolean(selectedTask.cancellation_requested_at)}>{selectedTask.cancellation_requested_at ? "等待取消" : "取消任务"}</button>}{canResearch && (selectedTask.status === "failed" || selectedTask.status === "cancelled") && <button onClick={() => taskAction("retry")} disabled={loading}>重新运行</button>}</div></div>
          {selectedTask.error_summary && <p className="error">{selectedTask.error_summary}</p>}
          <div className="repro-grid"><span><label>数据版本</label><b>{selectedTask.dataset_version}</b><small>{selectedTask.dataset_version_id}</small></span><span><label>因子版本</label><b>{selectedTask.factor_version}</b><small>{selectedTask.factor_version_id}</small></span><span><label>代码版本</label><b>{selectedTask.code_version}</b><small>实验创建时固定</small></span><span><label>执行时间</label><b>{formatTime(selectedTask.started_at)}</b><small>结束：{formatTime(selectedTask.finished_at)}</small></span></div>
          <h3>研究参数</h3><pre>{JSON.stringify(selectedTask.parameters, null, 2)}</pre>
          {selectedTask.result && <><div className="compact-metrics"><span><label>有效观测</label><b>{selectedTask.result.coverage}</b></span><span><label>IC均值</label><b>{number(selectedTask.result.ic_mean)}</b></span><span><label>Rank IC</label><b>{number(selectedTask.result.rank_ic_mean)}</b></span><span><label>ICIR</label><b>{number(selectedTask.result.icir)}</b></span><span><label>毛多空收益</label><b>{number(selectedTask.result.long_short_total_return, true)}</b></span><span><label>成本后多空收益</label><b>{number(selectedTask.result.long_short_net_total_return, true)}</b></span></div><h3>五分组平均收益</h3><div className="bars">{selectedTask.result.group_returns.map(item => <div className="bar-row" key={item.group}><span>Q{item.group}</span><div><i style={{width: `${Math.min(100, Math.abs(item.mean_return) * 4000 + 8)}%`}} /></div><strong>{number(item.mean_return, true)}</strong></div>)}</div></>}
          {taskConclusion && <section className={`conclusion ${taskConclusion.grade}`}><div className="section-title"><div><p className="eyebrow">RULE-BASED DRAFT · v{taskConclusion.method.version}</p><h3>结构化研究结论</h3></div><span>{taskConclusion.grade}</span></div><strong>{taskConclusion.headline}</strong><div className="conclusion-columns"><div><h3>支持证据</h3><ul>{taskConclusion.evidence.map(item => <li key={item}>{item}</li>)}</ul></div><div><h3>限制条件</h3><ul>{taskConclusion.limitations.map(item => <li key={item}>{item}</li>)}</ul></div><div><h3>建议下一步</h3><ol>{taskConclusion.next_steps.map(item => <li key={item}>{item}</li>)}</ol></div></div><small>{taskConclusion.disclaimer}</small></section>}
          <h3>执行日志</h3><div className="run-logs">{taskLogs.map(item => <div className={item.level} key={item.id}><time>{formatTime(item.created_at)}</time><b>{item.event}</b><span>{item.message}</span></div>)}{!taskLogs.length && <div className="empty">暂无日志。</div>}</div>
        </> : <div className="empty">从左侧选择一项任务查看详情。</div>}</div>
      </section>
    </> : view === "comparisons" ? <>
      <header><div><p className="eyebrow">EXPERIMENT COMPARISON</p><h1>让历史实验在同一张表里说话</h1><p>选择 2–6 个成功任务；首个选择作为差值基准，系统会检查数据版本、分组数和共同日期。</p></div><button onClick={runComparison} disabled={loading || comparisonRunIds.length < 2}>{loading ? "对比中…" : `生成对比（${comparisonRunIds.length}）`}</button></header>
      <section className="comparison-picker card">{tasks.filter(item => item.status === "success" && item.result).map(item => <label key={item.id} className={comparisonRunIds.includes(item.id) ? "selected" : ""}><input type="checkbox" checked={comparisonRunIds.includes(item.id)} onChange={() => toggleComparisonRun(item.id)} disabled={!comparisonRunIds.includes(item.id) && comparisonRunIds.length >= 6} /><span><b>{item.experiment_name}</b><small>{factorName(String(item.parameters?.factor ?? ""))} · 数据 {item.dataset_version} · {formatTime(item.finished_at)}</small></span></label>)}{!tasks.some(item => item.status === "success") && <div className="empty">至少完成两个研究任务后才能进行对比。</div>}</section>
      {comparison && <><section className={`comparison-summary card ${comparison.comparable ? "ready" : "warning"}`}><div><p className="eyebrow">COMPARABILITY CHECK</p><h2>{comparison.comparable ? "口径一致，可以直接比较" : "存在口径差异，请谨慎解释"}</h2></div><span>共同 IC 日期 <b>{comparison.common_ic_date_count}</b></span><div className="comparison-downloads"><button onClick={() => downloadComparison("csv")} disabled={loading}>下载 CSV</button><button onClick={() => downloadComparison("html")} disabled={loading}>下载 HTML 报告</button></div>{comparison.warnings.map(message => <p key={message}>{message}</p>)}</section><section className="card comparison-table"><div className="preview-scroll"><table><thead><tr><th>指标</th>{comparison.items.map((item, index) => <th key={item.run_id}>{item.experiment_name}<small>{index === 0 ? "基准" : factorName(item.factor)}</small></th>)}</tr></thead><tbody>{comparisonMetrics.map(([key, label, percent]) => <tr key={key}><th>{label}</th>{comparison.items.map((item, index) => <td key={item.run_id}><b>{key === "coverage" ? item.metrics[key] ?? "—" : number(item.metrics[key], percent)}</b>{index > 0 && <small>较基准 {number(item.delta_from_baseline[key], percent)}</small>}</td>)}</tr>)}</tbody></table></div></section><section className="comparison-rankings">{Object.entries(comparison.rankings).map(([metric, runIds]) => <article className="card" key={metric}><label>{comparisonMetrics.find(item => item[0] === metric)?.[1] ?? metric} 排名</label>{runIds.map((id, index) => { const item = comparison.items.find(value => value.run_id === id); return <span key={id}><b>{index + 1}</b>{item?.experiment_name}</span>; })}</article>)}</section></>}
      {comparison && <section className="card comparison-table" style={{marginTop: 16}}><h2>实际研究口径</h2><div className="preview-scroll"><table><thead><tr><th>任务</th><th>IC日期范围</th><th>证券筛选</th><th>价格口径</th><th>预处理</th><th>代码版本</th></tr></thead><tbody>{comparison.items.map(item => <tr key={item.run_id}><td>{item.experiment_name}<small>{item.run_id.slice(0, 8)}</small></td><td>{item.ic_start_date ?? "—"} 至 {item.ic_end_date ?? "—"}<small>{item.ic_date_count} 个截面</small></td><td>{item.sample_symbols.length ? item.sample_symbols.join(", ") : "数据集全部证券"}</td><td>{item.price_basis === "factor_adjusted" ? "close × adj_factor" : "导入的 close"}</td><td>{item.preprocessing.winsorize ? `MAD ${item.preprocessing.mad_scale}倍` : "不去极值"}<small>{item.preprocessing.standardize ? "Z-score标准化" : "不标准化"}</small></td><td>{item.code_version}</td></tr>)}</tbody></table></div></section>}
    </> : view === "users" && isAdmin ? <>
      <header><div><p className="eyebrow">ACCESS CONTROL</p><h1>少量研究人员账号管理</h1><p>由管理员创建账号、分配角色并控制启停；平台不开放自行注册。</p></div></header>
      <form className="card user-create" onSubmit={createPlatformUser}><div><label>用户名</label><input name="username" required pattern="[A-Za-z][A-Za-z0-9_]+" minLength={3} placeholder="researcher2" /></div><div><label>显示名称</label><input name="display_name" required placeholder="研究员二号" /></div><div><label>初始密码</label><input name="password" type="password" required minLength={10} placeholder="至少10位" /></div><div><label>角色</label><select name="role" defaultValue="researcher"><option value="researcher">研究员</option><option value="viewer">只读用户</option><option value="admin">管理员</option></select></div><button disabled={loading}>创建账号</button></form>
      <section className="card user-table"><div className="user-row heading"><span>用户</span><span>角色</span><span>状态</span><span>创建时间</span><span>操作</span></div>{users.map(item => <div className="user-row" key={item.id}><span><b>{item.display_name}</b><small>{item.username}</small></span><span><select value={item.role} disabled={loading || item.id === user.id} onChange={event => updatePlatformUser(item.id, { role: event.target.value })}><option value="admin">管理员</option><option value="researcher">研究员</option><option value="viewer">只读用户</option></select></span><span><i className={item.is_active ? "active" : "disabled"}>{item.is_active ? "已启用" : "已停用"}</i></span><span><small>{formatTime(item.created_at)}</small></span><span><button disabled={loading || item.id === user.id} onClick={() => updatePlatformUser(item.id, { is_active: !item.is_active })}>{item.is_active ? "停用" : "启用"}</button></span></div>)}</section>
    </> : <>
      <header><div><p className="eyebrow">REPORT ARCHIVE</p><h1>把结构化结果变成可交付报告</h1><p>每份报告都绑定唯一Run，可在线预览、下载并打印为PDF。</p></div>{selectedReport && <button className="download" onClick={downloadReport}>下载HTML</button>}</header>
      <section className="report-layout"><div className="card report-list">{reports.map(item => <button key={item.run_id} className={selectedReport?.run_id === item.run_id ? "selected" : ""} onClick={() => setSelectedReportId(item.run_id)}><strong>{item.experiment_name}</strong><span>数据 {item.dataset_version} · 因子 {item.factor_version}</span><small>{formatTime(item.created_at)}</small></button>)}{!reports.length && <div className="empty">成功完成研究后，报告会自动出现在这里。</div>}</div><div className="card report-preview">{selectedReport && reportHtml ? <iframe title={selectedReport.experiment_name} srcDoc={reportHtml} sandbox="allow-same-origin" /> : <div className="empty">暂无可预览报告。</div>}</div></section>
    </>}<footer>研究结果仅用于课程研究，不构成投资建议。</footer></main></div>;
}

createRoot(document.getElementById("root")!).render(<App />);
