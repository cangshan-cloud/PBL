import assert from "node:assert/strict";
import test from "node:test";
import { buildResearchConfiguration, longShortGroupLabel, resultForConfiguration } from "../src/research-config.ts";
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
});
