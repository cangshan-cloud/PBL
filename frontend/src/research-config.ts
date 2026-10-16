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
