import assert from "node:assert/strict";
import test from "node:test";
import { ACTIVE_TASK_REFRESH_MS, IDLE_TASK_REFRESH_MS, taskRefreshDelay } from "../src/task-refresh.ts";

test("task refresh remains fast while any task is pending or running", () => {
  assert.equal(taskRefreshDelay([{ status: "success" }, { status: "pending" }]), ACTIVE_TASK_REFRESH_MS);
  assert.equal(taskRefreshDelay([{ status: "running" }]), ACTIVE_TASK_REFRESH_MS);
});

test("finished, empty and failed loads use slower refresh", () => {
  assert.equal(taskRefreshDelay([{ status: "success" }, { status: "failed" }]), IDLE_TASK_REFRESH_MS);
  assert.equal(taskRefreshDelay([]), IDLE_TASK_REFRESH_MS);
  assert.equal(taskRefreshDelay(null), IDLE_TASK_REFRESH_MS);
});
