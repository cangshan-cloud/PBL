import assert from "node:assert/strict";
import test from "node:test";
import { pollResearchTask } from "../src/research-task.ts";

type Task = { status: string; id: string };
const pending: Task = { status: "pending", id: "run-1" };

test("polling publishes only current-session updates until completion", async () => {
  const updates: string[] = [];
  const states: Task[] = [{ ...pending, status: "running" }, { ...pending, status: "success" }];
  const result = await pollResearchTask(pending, async () => states.shift()!, task => updates.push(task.status), () => true, async () => undefined);
  assert.equal(result?.status, "success");
  assert.deepEqual(updates, ["running", "success"]);
});

test("session invalidated during delay makes no more requests", async () => {
  let current = true;
  let requests = 0;
  const result = await pollResearchTask(pending, async () => { requests += 1; return pending; }, () => assert.fail("stale update"), () => current, async () => { current = false; });
  assert.equal(result, null);
  assert.equal(requests, 0);
});

test("session invalidated during request discards late response", async () => {
  let current = true;
  let release!: (task: Task) => void;
  let requestStarted!: () => void;
  const started = new Promise<void>(resolve => { requestStarted = resolve; });
  const response = new Promise<Task>(resolve => { release = resolve; });
  const resultPromise = pollResearchTask(pending, () => { requestStarted(); return response; }, () => assert.fail("stale update"), () => current, async () => undefined);
  await started;
  current = false;
  release({ ...pending, status: "success" });
  assert.equal(await resultPromise, null);
});
