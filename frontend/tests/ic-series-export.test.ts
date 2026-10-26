import assert from "node:assert/strict";
import test from "node:test";
import { icSeriesCsv, icSeriesFilename } from "../src/ic-series-export.ts";

test("IC CSV preserves signed raw values, all dates, nulls and full Run identity", () => {
  const runId = "f424f62b-4081-400c-89ef-79bbff4a4e59";
  const csv = icSeriesCsv(runId, [
    { date: "2024-01-02", ic: -0.031415926535, rank_ic: 0.12 },
    { date: "2024-01-03", ic: null, rank_ic: -0.08 },
    { date: "2024-01-04", ic: null, rank_ic: null },
  ]);
  assert.equal(icSeriesFilename(runId), "ic-series-f424f62b.csv");
  assert.equal(csv.charCodeAt(0), 0xFEFF);
  assert.deepEqual(csv.slice(1).trimEnd().split("\r\n"), [
    "run_id,date,ic,rank_ic",
    `${runId},2024-01-02,-0.031415926535,0.12`,
    `${runId},2024-01-03,,-0.08`,
    `${runId},2024-01-04,,`,
  ]);
});

test("IC CSV treats unexpected text as data but retains negative numeric values", () => {
  const csv = icSeriesCsv("=FORMULA()", [
    { date: '+SUM(1),"quoted"', ic: -0.5, rank_ic: Number.NaN },
  ]);
  assert.match(csv, /'=FORMULA\(\)/);
  assert.match(csv, /"'\+SUM\(1\),""quoted"""/);
  assert.match(csv, /,-0\.5,\r\n/);
});

test("empty IC series still exports a valid header", () => {
  assert.equal(icSeriesCsv("run-1", []), "\uFEFFrun_id,date,ic,rank_ic\r\n");
});
