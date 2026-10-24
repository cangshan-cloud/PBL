export type ComparisonExportFormat = "csv" | "html" | "json";

export function comparisonDownloadFilename(format: ComparisonExportFormat, runIds: readonly string[]): string {
  const suffix = runIds.map(id => id.slice(0, 8)).join("-");
  return `factorlab-comparison-${suffix}.${format}`;
}

export function comparisonJsonContent(comparison: object): string {
  return `${JSON.stringify({ ...comparison, export_format: "factorlab-comparison", export_schema_version: 1 }, null, 2)}\n`;
}
