export function comparisonDelta(value: number | null | undefined, kind: "count" | "decimal" | "percent"): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const scaled = kind === "percent" ? value * 100 : value;
  const formatted = kind === "count" ? String(scaled) : scaled.toFixed(kind === "percent" ? 2 : 4);
  return `${scaled >= 0 ? "+" : ""}${formatted}${kind === "percent" ? "%" : ""}`;
}

export function comparisonDatasetLabel(version: string | undefined, id: string | undefined): string {
  return `数据 ${version ?? "—"}${id ? ` · ID ${id.slice(0, 8)}` : ""}`;
}

export function comparisonSourceLabel(kind: string | undefined): string {
  if (kind === "bundled_demo") return "内置演示数据";
  if (kind === "historical_bundle") return "历史研究数据包（来源另核）";
  if (kind === "imported_csv") return "导入 CSV（来源另核）";
  return "来源类别未记录";
}
