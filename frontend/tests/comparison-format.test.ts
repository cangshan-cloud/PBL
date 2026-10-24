import assert from "node:assert/strict";
import test from "node:test";
import { comparisonDatasetLabel, comparisonDelta, comparisonSourceLabel } from "../src/comparison-format.ts";

test("observation delta retains an integer count rather than four decimals", () => {
  assert.equal(comparisonDelta(-300, "count"), "-300");
  assert.equal(comparisonDelta(300, "count"), "+300");
});

test("IC and percentage deltas use the same precision as the HTML report", () => {
  assert.equal(comparisonDelta(0.00123, "decimal"), "+0.0012");
  assert.equal(comparisonDelta(0.125, "percent"), "+12.50%");
  assert.equal(comparisonDelta(0, "decimal"), "+0.0000");
});

test("unavailable and non-finite deltas remain missing", () => {
  assert.equal(comparisonDelta(null, "decimal"), "—");
  assert.equal(comparisonDelta(Number.NaN, "percent"), "—");
});

test("comparison picker distinguishes same version labels by dataset identity", () => {
  assert.equal(comparisonDatasetLabel("0.2.0", "aaaaaaaa-1111"), "数据 0.2.0 · ID aaaaaaaa");
  assert.equal(comparisonDatasetLabel("0.2.0", "bbbbbbbb-2222"), "数据 0.2.0 · ID bbbbbbbb");
  assert.equal(comparisonDatasetLabel(undefined, undefined), "数据 —");
});

test("source labels do not equate imported files with verified real market data", () => {
  assert.equal(comparisonSourceLabel("bundled_demo"), "内置演示数据");
  assert.equal(comparisonSourceLabel("historical_bundle"), "历史研究数据包（来源另核）");
  assert.equal(comparisonSourceLabel("imported_csv"), "导入 CSV（来源另核）");
  assert.equal(comparisonSourceLabel(undefined), "来源类别未记录");
});
