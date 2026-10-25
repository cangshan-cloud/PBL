import assert from "node:assert/strict";
import test from "node:test";
import { dailyCoverageCsv, dailyCoverageFilename } from "../src/daily-coverage-export.ts";
import { selectCoverageRows } from "../src/daily-coverage.ts";

test("daily coverage export retains all rows, raw ratios, nulls and run identity", () => {
  const runId = "321b313b-218a-41c1-a433-638550751caa";
  const csv = dailyCoverageCsv(runId, [
    { date: "2024-01-02", candidate_symbols: 300, eligible_symbols: 299, excluded_symbols: 1, coverage_ratio: 299 / 300, ic_status: "valid", group_status: "valid" },
    { date: "2024-01-03", eligible_symbols: 0, coverage_ratio: null, ic_status: "no_observation", group_status: "no_observation" },
  ]);
  assert.equal(dailyCoverageFilename(runId), "daily-coverage-321b313b.csv");
  assert.equal(csv.charCodeAt(0), 0xFEFF);
  const lines = csv.slice(1).trimEnd().split("\r\n");
  assert.equal(lines.length, 3);
  assert.equal(lines[0], "run_id,date,candidate_symbols,eligible_symbols,coverage_ratio,excluded_symbols,ic_status,group_status");
  assert.equal(lines[1], `${runId},2024-01-02,300,299,${299 / 300},1,valid,valid`);
  assert.equal(lines[2], `${runId},2024-01-03,,0,,,no_observation,no_observation`);
});

test("daily coverage export escapes spreadsheet formulas, commas and quotes", () => {
  const csv = dailyCoverageCsv("=malicious", [
    { date: '2024-01-02, "bad"', eligible_symbols: 0, ic_status: "+SUM(1)", group_status: "valid" },
  ]);
  assert.match(csv, /^\uFEFFrun_id/);
  assert.match(csv, /'=malicious/);
  assert.match(csv, /"2024-01-02, ""bad"""/);
  assert.match(csv, /'\+SUM\(1\)/);
});

test("full export is independent of the optional review filter", () => {
  const rows = [
    { date: "2024-01-02", eligible_symbols: 300, excluded_symbols: 0, ic_status: "valid", group_status: "valid" },
    { date: "2024-01-03", eligible_symbols: 299, excluded_symbols: 1, ic_status: "valid", group_status: "valid" },
  ];
  assert.equal(selectCoverageRows(rows, true).length, 1);
  const csv = dailyCoverageCsv("run-1", rows);
  assert.match(csv, /2024-01-02/);
  assert.match(csv, /2024-01-03/);
});
