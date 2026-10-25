import assert from "node:assert/strict";
import test from "node:test";
import { selectCoveragePage } from "../src/daily-coverage.ts";

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
