import assert from "node:assert/strict";
import test from "node:test";
import { buildResearchConfiguration, longShortGroupLabel, resultForConfiguration, validateResearchConfiguration } from "../src/research-config.ts";
import type { ResearchConfigurationInput } from "../src/research-config.ts";

const base: ResearchConfigurationInput = {
  mode: "single",
  datasetId: "data-1",
  factorId: "momentum_20d",
  factorDefaultLookback: 20,
  compositeFactors: ["momentum_20d", "reversal_5d"],
  lookback: 20,
  groups: 5,
  winsorize: true,
  standardize: true,
  transactionCostBps: 10,
  priceBasis: "source_close",
  sampleStart: "2025-01-01",
  sampleEnd: "2025-06-30",
  validationStart: "",
  sampleSymbols: "000001.SZ, 600000.SH",
};

test("single-factor key is built from the exact submitted parameters", () => {
  const { parameters, key } = buildResearchConfiguration(base);
  assert.deepEqual(parameters, {
    factor: "momentum_20d",
    dataset_version_id: "data-1",
    groups: 5,
    winsorize: true,
    standardize: true,
    mad_scale: 3,
    transaction_cost_bps: 10,
    price_basis: "source_close",
    start_date: "2025-01-01",
    end_date: "2025-06-30",
    symbols: ["000001.SZ", "600000.SH"],
    lookback: 20,
  });
  assert.deepEqual(JSON.parse(key), { mode: "single", parameters });
});

test("result is hidden when factor, dataset, sample, groups, price basis, or preprocessing changes", () => {
  const original = buildResearchConfiguration(base);
  const task = { id: "run-1" };
  assert.equal(resultForConfiguration(task, original.key, original.key), task);
  const changed: Partial<ResearchConfigurationInput>[] = [
    { factorId: "reversal_5d" },
    { datasetId: "data-2" },
    { sampleStart: "2025-02-01" },
    { sampleEnd: "2025-05-31" },
    { validationStart: "2025-04-01" },
    { sampleSymbols: "000001.SZ" },
    { groups: 3 },
    { lookback: 25 },
    { priceBasis: "factor_adjusted" },
    { winsorize: false },
    { standardize: false },
    { transactionCostBps: 15 },
  ];
  for (const change of changed) {
    const current = buildResearchConfiguration({ ...base, ...change });
    assert.notEqual(current.key, original.key);
    assert.equal(resultForConfiguration(task, original.key, current.key), null);
  }
});

test("ordinary symbol separator differences normalize to the same submitted payload", () => {
  const comma = buildResearchConfiguration(base);
  const whitespace = buildResearchConfiguration({ ...base, sampleSymbols: "000001.SZ;600000.SH" });
  assert.equal(comma.key, whitespace.key);
});

test("historical mode uses only its actual API parameters", () => {
  const original = buildResearchConfiguration({ ...base, mode: "historical", factorId: null });
  const hiddenOrdinaryChange = buildResearchConfiguration({ ...base, mode: "historical", factorId: "other", priceBasis: "factor_adjusted" });
  assert.deepEqual(original.parameters, { dataset_version_id: "data-1", groups: 5 });
  assert.equal(original.key, hiddenOrdinaryChange.key);
  const split = buildResearchConfiguration({ ...base, mode: "historical", historicalSplitEnabled: true });
  assert.deepEqual(split.parameters, { dataset_version_id: "data-1", groups: 5, validation_start_date: "2024-07-01" });
  assert.notEqual(split.key, original.key);
  assert.equal(validateResearchConfiguration({ ...base, mode: "historical", historicalSplitEnabled: true }), null);
});

test("mode and composite component changes produce distinct result keys", () => {
  const single = buildResearchConfiguration(base);
  const composite = buildResearchConfiguration({ ...base, mode: "composite" });
  const changedComponents = buildResearchConfiguration({ ...base, mode: "composite", compositeFactors: ["momentum_20d", "volatility_20d"] });
  assert.notEqual(single.key, composite.key);
  assert.notEqual(composite.key, changedComponents.key);
  assert.deepEqual(composite.parameters?.factors, ["momentum_20d", "reversal_5d"]);
});

test("single-factor without a lookback and missing prerequisites", () => {
  const noWindow = buildResearchConfiguration({ ...base, factorDefaultLookback: null });
  assert.equal("lookback" in noWindow.parameters!, false);
  assert.equal(buildResearchConfiguration({ ...base, datasetId: null }).parameters, null);
  assert.equal(buildResearchConfiguration({ ...base, factorId: null }).parameters, null);
});

test("group label follows the selected group count", () => {
  assert.equal(longShortGroupLabel(3), "Q3 − Q1");
  assert.equal(longShortGroupLabel(5), "Q5 − Q1");
  assert.equal(longShortGroupLabel(0), "—");
  assert.equal(longShortGroupLabel(NaN), "—");
});

test("invalid numeric research inputs are rejected before submission", () => {
  for (const groups of [NaN, 1, 11, 2.5]) assert.match(validateResearchConfiguration({ ...base, groups })!, /分组数量/);
  for (const lookback of [NaN, 1, 121, 2.5]) assert.match(validateResearchConfiguration({ ...base, lookback })!, /回看窗口/);
  for (const transactionCostBps of [NaN, Infinity, -1, 101]) assert.match(validateResearchConfiguration({ ...base, transactionCostBps })!, /单边成本/);
  assert.equal(validateResearchConfiguration({ ...base, factorDefaultLookback: null, lookback: NaN }), null);
  assert.equal(validateResearchConfiguration({ ...base, mode: "historical", lookback: NaN, transactionCostBps: NaN }), null);
});

test("adjusted adapter prices cannot be adjusted again before submission", () => {
  for (const mode of ["single", "composite"] as const) {
    for (const flag of ["1", "2"]) {
      assert.match(validateResearchConfiguration({ ...base, mode, priceBasis: "factor_adjusted", sourceAdjustmentFlags: [flag] })!, /不能再次选择/);
    }
    assert.equal(validateResearchConfiguration({ ...base, mode, priceBasis: "source_close", sourceAdjustmentFlags: ["2"] }), null);
    assert.equal(validateResearchConfiguration({ ...base, mode, priceBasis: "factor_adjusted", sourceAdjustmentFlags: ["3"] }), null);
    assert.match(validateResearchConfiguration({ ...base, mode, priceBasis: "factor_adjusted", sourceAdjustmentFlags: "3" })!, /状态不明确/);
  }
  assert.equal(validateResearchConfiguration({ ...base, mode: "historical", priceBasis: "factor_adjusted", sourceAdjustmentFlags: ["2"] }), null);
});

test("factor-adjusted basis requires the multiplier column before submission", () => {
  for (const mode of ["single", "composite"] as const) {
    assert.match(validateResearchConfiguration({ ...base, mode, priceBasis: "factor_adjusted", datasetColumns: ["trade_date", "symbol", "close"] })!, /缺少 adj_factor 列/);
    assert.match(validateResearchConfiguration({ ...base, mode, priceBasis: "factor_adjusted", datasetColumns: ["close"], sourceAdjustmentFlags: ["3"] })!, /缺少 adj_factor 列/);
    assert.equal(validateResearchConfiguration({ ...base, mode, priceBasis: "factor_adjusted", datasetColumns: ["close", "adj_factor"], sourceAdjustmentFlags: ["3"] }), null);
    assert.equal(validateResearchConfiguration({ ...base, mode, priceBasis: "source_close", datasetColumns: ["close"] }), null);
  }
});

test("missing multiplier values block only an unfiltered adjusted-price study", () => {
  for (const mode of ["single", "composite"] as const) {
    const input = { ...base, mode, priceBasis: "factor_adjusted" as const, datasetColumns: ["close", "adj_factor"], missingAdjustmentCount: 1, sampleSymbols: "" };
    assert.match(validateResearchConfiguration(input)!, /研究全部证券会失败/);
    assert.equal(validateResearchConfiguration({ ...input, sampleSymbols: "000001.SZ,000002.SZ" }), null);
    assert.equal(validateResearchConfiguration({ ...input, priceBasis: "source_close" }), null);
    assert.equal(validateResearchConfiguration({ ...input, missingAdjustmentCount: 0 }), null);
  }
});

test("new dataset symbol-level multiplier evidence rejects only affected selections", () => {
  const input = { ...base, priceBasis: "factor_adjusted" as const, datasetColumns: ["close", "adj_factor"],
    missingAdjustmentCount: 2, missingAdjustmentBySymbol: { "000002.SZ": 2 }, sampleSymbols: "000001.SZ;000002.SZ" };
  assert.match(validateResearchConfiguration(input)!, /所选证券存在缺失/);
  assert.equal(validateResearchConfiguration({ ...input, sampleSymbols: "000001.SZ,000003.SZ" }), null);
  assert.equal(validateResearchConfiguration({ ...input, missingAdjustmentBySymbol: undefined }), null);
  assert.equal(validateResearchConfiguration({ ...input, priceBasis: "source_close" }), null);
});

test("invalid samples and component counts are rejected before submission", () => {
  assert.match(validateResearchConfiguration({ ...base, sampleStart: "2025-07-01" })!, /起始日不能晚于结束日/);
  assert.match(validateResearchConfiguration({ ...base, sampleStart: "2024-12-31" }, "2025-01-01", "2025-06-30")!, /早于数据起点/);
  assert.match(validateResearchConfiguration({ ...base, sampleStart: "2025-07-01", sampleEnd: "" }, "2025-01-01", "2025-06-30")!, /起始日不能晚于数据终点/);
  assert.match(validateResearchConfiguration({ ...base, sampleStart: "", sampleEnd: "2024-12-31" }, "2025-01-01", "2025-06-30")!, /结束日不能早于数据起点/);
  assert.match(validateResearchConfiguration({ ...base, sampleEnd: "2025-07-01" }, "2025-01-01", "2025-06-30")!, /晚于数据终点/);
  assert.match(validateResearchConfiguration({ ...base, mode: "composite", compositeFactors: ["momentum_20d"] })!, /2～6 个因子/);
  assert.match(validateResearchConfiguration({ ...base, validationStart: "2025-01-01" })!, /验证起始日必须晚于/);
  assert.match(validateResearchConfiguration({ ...base, validationStart: "2025-07-01" })!, /验证起始日不能晚于/);
  assert.equal(buildResearchConfiguration({ ...base, validationStart: "2025-04-01" }).parameters?.validation_start_date, "2025-04-01");
  assert.equal(validateResearchConfiguration(base, "2025-01-01", "2025-06-30"), null);
});
