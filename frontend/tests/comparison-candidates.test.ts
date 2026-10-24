import assert from "node:assert/strict";
import test from "node:test";
import { comparisonCandidateHint } from "../src/comparison-candidates.ts";

test("comparison candidates distinguish loading from an empty history", () => {
  assert.equal(comparisonCandidateHint([], true), "正在刷新研究任务候选…");
  assert.equal(comparisonCandidateHint([], false), "至少完成两个研究任务后才能进行对比。");
});

test("comparison candidates explain an in-flight run and clear the hint after success", () => {
  const first = { status: "success", result: {} };
  assert.equal(comparisonCandidateHint([first, { status: "running" }], false), "研究任务仍在执行，成功后候选会自动更新。");
  assert.equal(comparisonCandidateHint([first], false), "还需完成一项研究任务才能生成对比。");
  assert.equal(comparisonCandidateHint([first, { status: "success", result: {} }], false), null);
});
