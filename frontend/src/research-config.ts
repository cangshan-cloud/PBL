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
  sourceAdjustmentFlags?: unknown;
  datasetColumns?: string[];
  missingAdjustmentCount?: number;
  missingAdjustmentBySymbol?: Record<string, number>;
  sampleStart: string;
  sampleEnd: string;
  validationStart: string;
  historicalSplitEnabled?: boolean;
  sampleSymbols: string;
};

export function validateResearchConfiguration(
  input: ResearchConfigurationInput,
  datasetStart: string | null = null,
  datasetEnd: string | null = null,
): string | null {
  if (!Number.isInteger(input.groups) || input.groups < 2 || input.groups > 10) return "分组数量须为 2～10 的整数";
  if (input.mode === "historical") return null;
  if (input.priceBasis === "factor_adjusted" && input.sourceAdjustmentFlags &&
      (!Array.isArray(input.sourceAdjustmentFlags) ||
       (input.sourceAdjustmentFlags.length > 0 &&
        (input.sourceAdjustmentFlags.length !== 1 || input.sourceAdjustmentFlags[0] !== "3")))) {
    return "当前数据版本的来源价格已复权或复权状态不明确，不能再次选择 close × adj_factor；请使用导入的 close";
  }
  if (input.priceBasis === "factor_adjusted" && input.datasetColumns && !input.datasetColumns.includes("adj_factor")) {
    return "当前数据版本缺少 adj_factor 列，不能选择 close × adj_factor；请使用导入的 close";
  }
  if (input.priceBasis === "factor_adjusted" && !input.sampleSymbols.trim() &&
      typeof input.missingAdjustmentCount === "number" && input.missingAdjustmentCount > 0) {
    return "当前数据版本有缺失的 adj_factor；研究全部证券会失败。请选择乘数完整的证券样本，或使用导入的 close";
  }
  if (input.priceBasis === "factor_adjusted" && input.sampleSymbols.trim() && input.missingAdjustmentBySymbol &&
      input.sampleSymbols.split(/[\s,;]+/).some(symbol => (input.missingAdjustmentBySymbol?.[symbol.trim()] ?? 0) > 0)) {
    return "所选证券存在缺失的 adj_factor；请选择乘数完整的证券，或使用导入的 close";
  }
  if (input.mode === "single" && input.factorDefaultLookback !== null &&
      (!Number.isInteger(input.lookback) || input.lookback < 2 || input.lookback > 120)) return "回看窗口须为 2～120 的整数";
  if (input.mode === "composite" && (input.compositeFactors.length < 2 || input.compositeFactors.length > 6)) return "等权多因子须选择 2～6 个因子";
  if (!Number.isFinite(input.transactionCostBps) || input.transactionCostBps < 0 || input.transactionCostBps > 100) return "单边成本须在 0～100 bps 之间";
  if (input.sampleStart && input.sampleEnd && input.sampleStart > input.sampleEnd) return "因子起始日不能晚于结束日";
  if (input.validationStart && input.sampleStart && input.validationStart <= input.sampleStart) return "验证起始日必须晚于因子起始日";
  if (input.validationStart && input.sampleEnd && input.validationStart > input.sampleEnd) return "验证起始日不能晚于因子结束日";
  if (datasetStart && input.validationStart && input.validationStart <= datasetStart) return `验证起始日必须晚于数据起点 ${datasetStart}`;
  if (datasetEnd && input.validationStart && input.validationStart > datasetEnd) return `验证起始日不能晚于数据终点 ${datasetEnd}`;
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
    ...(input.validationStart ? { validation_start_date: input.validationStart } : {}),
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
    ? { dataset_version_id: datasetId, groups,
        ...(input.historicalSplitEnabled ? { validation_start_date: "2024-07-01" } : {}) }
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
  return Number.isInteger(groups) && groups >= 2 && groups <= 10 ? `Q${groups} − Q1` : "—";
}
