import assert from "node:assert/strict";
import test from "node:test";
import { longShortCsv, longShortFilename } from "../src/long-short-export.ts";

test("long-short CSV preserves saved ratios, NAV, cost and full Run identity", () => {
  const runId = "858c2667-19b8-4538-a02b-a3a16175adf5";
  const csv = longShortCsv(runId, 10, [
    { date: "2024-01-02", return: -0.0123456789, nav: 0.9876543211, turnover: 2, cost: 0.002, net_return: -0.0143456789, net_nav: 0.9856543211 },
    { date: "2024-01-03", return: 0.005, nav: 0.9925925927055, turnover: 0, cost: 0, net_return: 0.005, net_nav: 0.9905825927055 },
  ]);
  assert.equal(longShortFilename(runId), "long-short-858c2667.csv");
  assert.equal(csv.charCodeAt(0), 0xFEFF);
  assert.deepEqual(csv.slice(1).trimEnd().split("\r\n"), [
    "run_id,date,gross_return,gross_nav,two_side_turnover,cost,net_return,net_nav,transaction_cost_bps",
    `${runId},2024-01-02,-0.0123456789,0.9876543211,2,0.002,-0.0143456789,0.9856543211,10`,
    `${runId},2024-01-03,0.005,0.9925925927055,0,0,0.005,0.9905825927055,10`,
  ]);
});

test("long-short CSV remains header-only when no date can form groups", () => {
  assert.equal(longShortCsv("run-1", 10, []), "\uFEFFrun_id,date,gross_return,gross_nav,two_side_turnover,cost,net_return,net_nav,transaction_cost_bps\r\n");
});

test("long-short CSV escapes unexpected text without changing signed numbers", () => {
  const csv = longShortCsv("=FORMULA()", 0, [
    { date: '+SUM(1),"quoted"', return: -0.1, nav: 0.9, turnover: 0, cost: 0, net_return: -0.1, net_nav: 0.9 },
  ]);
  assert.match(csv, /'=FORMULA\(\)/);
  assert.match(csv, /"'\+SUM\(1\),""quoted"""/);
  assert.match(csv, /,-0\.1,0\.9,0,0,-0\.1,0\.9,0\r\n/);
});
