import assert from "node:assert/strict";
import test from "node:test";
import { alignNavLines } from "../src/chart-series.ts";

test("NAV lines share ordered dates and break rather than bridge absent dates", () => {
  const aligned = alignNavLines([
    { label: "Q1", color: "green", points: [
      { date: "2024-01-02", value: 1.01 }, { date: "2024-01-04", value: 1.03 },
    ] },
    { label: "Q2", color: "blue", points: [
      { date: "2024-01-03", value: 0.99 }, { date: "2024-01-04", value: 1.02 },
    ] },
  ]);
  assert.deepEqual(aligned.dates, ["2024-01-02", "2024-01-03", "2024-01-04"]);
  assert.deepEqual(aligned.lines[0].segments, [[{ index: 0, value: 1.01 }], [{ index: 2, value: 1.03 }]]);
  assert.deepEqual(aligned.lines[1].segments, [[{ index: 1, value: 0.99 }, { index: 2, value: 1.02 }]]);
  assert.equal(aligned.lines[0].lastValue, 1.03);
});

test("non-finite points break a line and empty series has no last value", () => {
  const aligned = alignNavLines([
    { label: "gross", color: "green", points: [
      { date: "2024-01-02", value: 1 }, { date: "2024-01-03", value: Number.NaN },
      { date: "2024-01-04", value: 0.98 },
    ] },
    { label: "net", color: "orange", points: [] },
  ]);
  assert.deepEqual(aligned.lines[0].segments, [[{ index: 0, value: 1 }], [{ index: 2, value: 0.98 }]]);
  assert.equal(aligned.lines[1].lastValue, null);
  assert.deepEqual(aligned.lines[1].segments, []);
});

test("known diagnostic date breaks even when every saved line lacks that date", () => {
  const aligned = alignNavLines([
    { label: "IC", color: "green", points: [
      { date: "2025-01-02", value: 0.1 }, { date: "2025-01-06", value: 0.2 },
    ] },
  ], ["2025-01-03"]);
  assert.deepEqual(aligned.dates, ["2025-01-02", "2025-01-03", "2025-01-06"]);
  assert.deepEqual(aligned.lines[0].segments, [[{ index: 0, value: 0.1 }], [{ index: 2, value: 0.2 }]]);
  assert.equal(aligned.lines[0].lastValue, 0.2);
});
