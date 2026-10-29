import assert from "node:assert/strict";
import test from "node:test";
import { componentIcCsv, componentIcFilename } from "../src/component-ic-export.ts";

test("component IC CSV binds full Run and preserves raw signed values, counts and nulls", () => {
  const runId = "9bbb1f11-548d-423c-a56c-ced6eb70d545";
  const csv = componentIcCsv(runId, 72366, [
    { factor: "momentum_20d", ic_mean: 0.008943096712500317, rank_ic_mean: 0.000512273381447914, valid_ic_dates: 242, signal_date_count: 242 },
    { factor: "constant", ic_mean: null, rank_ic_mean: null, valid_ic_dates: 0, signal_date_count: 242 },
  ]);
  assert.equal(componentIcFilename(runId), "component-ic-9bbb1f11.csv");
  assert.equal(csv.charCodeAt(0), 0xFEFF);
  assert.deepEqual(csv.slice(1).trimEnd().split("\r\n"), [
    "run_id,factor,ic_mean,rank_ic_mean,valid_ic_dates,signal_date_count,common_coverage",
    `${runId},momentum_20d,0.008943096712500317,0.000512273381447914,242,242,72366`,
    `${runId},constant,,,0,242,72366`,
  ]);
});

test("component IC CSV protects spreadsheet cells supplied as text", () => {
  const csv = componentIcCsv("=RUN()", 1, [
    { factor: '+SUM(1),"quoted"', ic_mean: -0.5, rank_ic_mean: null, valid_ic_dates: 1, signal_date_count: 1 },
  ]);
  assert.match(csv, /'=RUN\(\)/);
  assert.match(csv, /"'\+SUM\(1\),""quoted"""/);
  assert.match(csv, /,-0\.5,,1,1,1\r\n/);
});
