export type ResearchMode = "single" | "composite" | "historical";
export type PriceBasis = "source_close" | "factor_adjusted";

export type ResearchConfigurationInput = {
  mode: ResearchMode;
  datasetId: string | null;
  factorId: string | null;
  factorDefaultLookback: number | null;
  compositeFactors: string[];
  lookback: number;
  groups: number;
  winsorize: boolean;
  standardize: boolean;
  transactionCostBps: number;
  priceBasis: PriceBasis;
  sampleStart: string;
  sampleEnd: string;
  sampleSymbols: string;
};

export function validateResearchConfiguration(
  input: ResearchConfigurationInput,
  datasetStart: string | null = null,
  datasetEnd: string | null = null,
): string | null {
  if (!Number.isInteger(input.groups) || input.groups < 2 || input.groups > 10) return "分组数量须为 2～10 的整数";
  if (input.mode === "historical") return null;
  if (input.mode === "single" && input.factorDefaultLookback !== null &&
      (!Number.isInteger(input.lookback) || input.lookback < 2 || input.lookback > 120)) return "回看窗口须为 2～120 的整数";
  if (input.mode === "composite" && (input.compositeFactors.length < 2 || input.compositeFactors.length > 6)) return "等权多因子须选择 2～6 个因子";
  if (!Number.isFinite(input.transactionCostBps) || input.transactionCostBps < 0 || input.transactionCostBps > 100) return "单边成本须在 0～100 bps 之间";
  if (input.sampleStart && input.sampleEnd && input.sampleStart > input.sampleEnd) return "因子起始日不能晚于结束日";
  if (datasetStart && input.sampleStart && input.sampleStart < datasetStart) return `因子起始日不能早于数据起点 ${datasetStart}`;
  if (datasetEnd && input.sampleStart && input.sampleStart > datasetEnd) return `因子起始日不能晚于数据终点 ${datasetEnd}`;
  if (datasetStart && input.sampleEnd && input.sampleEnd < datasetStart) return `因子结束日不能早于数据起点 ${datasetStart}`;
  if (datasetEnd && input.sampleEnd && input.sampleEnd > datasetEnd) return `因子结束日不能晚于数据终点 ${datasetEnd}`;
  return null;
}

export function buildResearchConfiguration(input: ResearchConfigurationInput): {
  parameters: Record<string, unknown> | null;
  key: string;
} {
  const { mode, datasetId, groups } = input;
  const symbols = input.sampleSymbols.split(/[\s,;]+/).map(value => value.trim()).filter(Boolean);
  const sample = {
    start_date: input.sampleStart || null,
    end_date: input.sampleEnd || null,
    symbols: symbols.length ? symbols : null,
  };
  const ordinary = {
    dataset_version_id: datasetId,
    groups,
    winsorize: input.winsorize,
    standardize: input.standardize,
    mad_scale: 3,
    transaction_cost_bps: input.transactionCostBps,
    price_basis: input.priceBasis,
    ...sample,
  };
  const parameters: Record<string, unknown> | null = !datasetId ? null : mode === "historical"
    ? { dataset_version_id: datasetId, groups }
    : mode === "composite"
    ? { factors: [...input.compositeFactors], ...ordinary }
    : !input.factorId ? null
    : { factor: input.factorId, ...ordinary, ...(input.factorDefaultLookback !== null ? { lookback: input.lookback } : {}) };
  return { parameters, key: JSON.stringify({ mode, parameters }) };
}

export function resultForConfiguration<T>(task: T | null, submittedKey: string, currentKey: string): T | null {
  return submittedKey === currentKey ? task : null;
}

export function longShortGroupLabel(groups: number): string {
  return `Q${groups} − Q1`;
}
