import assert from "node:assert/strict";
import test from "node:test";
import { needsCoverageReview, selectCoveragePage, selectCoverageRows, type DailyCoverageRow } from "../src/daily-coverage.ts";

test("daily coverage pages retain all dates without overlap", () => {
  const rows = Array.from({ length: 242 }, (_, index) => index);
  const pages = Array.from({ length: 13 }, (_, page) => selectCoveragePage(rows, page));
  assert.deepEqual(pages.flatMap(item => item.rows), rows);
  assert.equal(pages[0].rows.length, 20);
  assert.equal(pages.at(-1)?.rows.length, 2);
  assert.equal(pages.at(-1)?.pageCount, 13);
});

test("daily coverage clamps stale page state and handles empty input", () => {
  assert.deepEqual(selectCoveragePage([1, 2], 50).rows, [1, 2]);
  assert.equal(selectCoveragePage([1, 2], 50).page, 0);
  assert.equal(selectCoveragePage([], -5).end, 0);
  assert.throws(() => selectCoveragePage([1], 0, 0), RangeError);
});

test("review filter retains only coverage gaps or noncomputable sections in source order", () => {
  const rows: DailyCoverageRow[] = [
    { date: "2024-01-02", eligible_symbols: 300, excluded_symbols: 0, ic_status: "valid", group_status: "valid" },
    { date: "2024-01-03", eligible_symbols: 299, excluded_symbols: 1, ic_status: "valid", group_status: "valid" },
    { date: "2024-01-04", eligible_symbols: 300, ic_status: "constant_factor", group_status: "valid" },
    { date: "2024-01-05", eligible_symbols: 300, ic_status: "valid", group_status: "insufficient_sample" },
  ];
  assert.equal(needsCoverageReview(rows[0]), false);
  assert.deepEqual(selectCoverageRows(rows, true).map(row => row.date), ["2024-01-03", "2024-01-04", "2024-01-05"]);
  assert.equal(selectCoverageRows(rows, false), rows);
  assert.deepEqual(selectCoveragePage(selectCoverageRows(rows, true), 8).rows.map(row => row.date), ["2024-01-03", "2024-01-04", "2024-01-05"]);
});
