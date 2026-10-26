import assert from "node:assert/strict";
import test from "node:test";
import { filterReports, reportListHint, selectVisibleReport } from "../src/report-list.ts";

test("report list distinguishes initial loading from an empty archive", () => {
  assert.equal(reportListHint(0, true), "正在刷新研究报告…");
  assert.equal(reportListHint(0, false), "成功完成研究后，报告会自动出现在这里。");
  assert.equal(reportListHint(1, true), null);
  assert.equal(reportListHint(1, false), null);
});

const reports = [
  { run_id: "ABC-001", experiment_name: "动量研究" },
  { run_id: "def-002", experiment_name: "价值研究" },
  { run_id: "ghi-003", experiment_name: "动量复核" },
];

test("report search matches name or Run ID without changing archive order", () => {
  assert.deepEqual(filterReports(reports, " 动量 ").map(item => item.run_id), ["ABC-001", "ghi-003"]);
  assert.deepEqual(filterReports(reports, "DEF").map(item => item.run_id), ["def-002"]);
  assert.deepEqual(filterReports(reports, " "), reports);
});

test("report selection stays within visible matches and clears on zero matches", () => {
  const matched = filterReports(reports, "动量");
  assert.equal(selectVisibleReport(matched, "ghi-003")?.run_id, "ghi-003");
  assert.equal(selectVisibleReport(matched, "def-002")?.run_id, "ABC-001");
  assert.equal(selectVisibleReport(filterReports(reports, "not-found"), "ABC-001"), undefined);
});

test("full Run query disambiguates same-name reports and cannot fall back to another archive", () => {
  const sameName = [
    { run_id: "run-111", experiment_name: "重复名称" },
    { run_id: "run-222", experiment_name: "重复名称" },
  ];
  assert.equal(selectVisibleReport(filterReports(sameName, "run-222"), "run-222")?.run_id, "run-222");
  assert.equal(selectVisibleReport(filterReports(sameName, "run-333"), "run-333"), undefined);
});
