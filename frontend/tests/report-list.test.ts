import assert from "node:assert/strict";
import test from "node:test";
import { reportListHint } from "../src/report-list.ts";

test("report list distinguishes initial loading from an empty archive", () => {
  assert.equal(reportListHint(0, true), "正在刷新研究报告…");
  assert.equal(reportListHint(0, false), "成功完成研究后，报告会自动出现在这里。");
  assert.equal(reportListHint(1, true), null);
  assert.equal(reportListHint(1, false), null);
});
