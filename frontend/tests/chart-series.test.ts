import assert from "node:assert/strict";
import test from "node:test";
import { alignNavLines, icChartLines, icInspectionRows, interiorAllMissingDates, navInspectionRows } from "../src/chart-series.ts";

test("NAV inspection aligns saved groups without filling absent values", () => {
  assert.deepEqual(navInspectionRows([
    { label: "Q1", color: "green", points: [{ date: "2025-01-02", value: 1.123456789 }, { date: "2025-01-06", value: 1.2 }] },
    { label: "Q2", color: "orange", points: [{ date: "2025-01-03", value: 0.9 }, { date: "2025-01-06", value: Number.NaN }] },
  ], ["2025-01-04"]), [
    { date: "2025-01-02", values: [{ label: "Q1", value: 1.123456789 }, { label: "Q2", value: null }], hasRecord: true },
    { date: "2025-01-03", values: [{ label: "Q1", value: null }, { label: "Q2", value: 0.9 }], hasRecord: true },
    { date: "2025-01-04", values: [{ label: "Q1", value: null }, { label: "Q2", value: null }], hasRecord: false },
    { date: "2025-01-06", values: [{ label: "Q1", value: 1.2 }, { label: "Q2", value: null }], hasRecord: true },
  ]);
});

test("IC date inspection preserves saved precision and known diagnostic-only dates", () => {
  assert.deepEqual(icInspectionRows([
    { date: "2025-01-03", ic: null, rank_ic: 0.123456789 },
    { date: "2025-01-02", ic: -0.5, rank_ic: null },
  ], ["2025-01-06", "2025-01-03"]), [
    { date: "2025-01-02", ic: -0.5, rank_ic: null, hasRecord: true },
    { date: "2025-01-03", ic: null, rank_ic: 0.123456789, hasRecord: true },
    { date: "2025-01-06", ic: null, rank_ic: null, hasRecord: false },
  ]);
  assert.deepEqual(icInspectionRows([], []), []);
});

test("IC and Rank IC use separate saved values, gaps, and last finite points", () => {
  const series = [
    { date: "2025-01-02", ic: 0.1, rank_ic: -0.2 },
    { date: "2025-01-03", ic: null, rank_ic: 0.3 },
    { date: "2025-01-06", ic: -0.1, rank_ic: null },
  ];
  const aligned = alignNavLines(icChartLines(series), ["2025-01-07"]);
  assert.deepEqual(aligned.lines.map(line => line.label), ["IC", "Rank IC"]);
  assert.deepEqual(aligned.lines[0].segments, [[{ index: 0, value: 0.1 }], [{ index: 2, value: -0.1 }]]);
  assert.deepEqual(aligned.lines[1].segments, [[{ index: 0, value: -0.2 }, { index: 1, value: 0.3 }]]);
  assert.deepEqual(aligned.lines.map(line => line.lastValue), [-0.1, 0.3]);
  assert.deepEqual(interiorAllMissingDates(aligned), []);
});

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
  assert.deepEqual(interiorAllMissingDates(aligned), ["2025-01-03"]);
});

test("gap notice lists only internal dates where every line is absent", () => {
  const aligned = alignNavLines([
    { label: "Q1", color: "green", points: [
      { date: "2025-01-02", value: 1 }, { date: "2025-01-04", value: 1.02 },
    ] },
    { label: "Q2", color: "blue", points: [
      { date: "2025-01-03", value: 1.01 }, { date: "2025-01-07", value: 1.03 },
    ] },
  ], ["2025-01-01", "2025-01-06", "2025-01-08"]);
  assert.deepEqual(interiorAllMissingDates(aligned), ["2025-01-06"]);
  assert.deepEqual(interiorAllMissingDates(alignNavLines([], ["2025-01-02"])), []);
  assert.deepEqual(interiorAllMissingDates(alignNavLines([
    { label: "IC", color: "green", points: [{ date: "2025-01-02", value: 0.1 }] },
  ], ["2025-01-03"])), []);
});
