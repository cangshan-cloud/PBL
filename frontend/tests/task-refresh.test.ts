import assert from "node:assert/strict";
import test from "node:test";
import { ACTIVE_TASK_REFRESH_MS, IDLE_TASK_REFRESH_MS, startTaskPolling, taskRefreshDelay, type TaskPollClock } from "../src/task-refresh.ts";

function fakeClock() {
  let next = 1;
  const scheduled = new Map<number, { callback: () => void; delayMs: number }>();
  const clock: TaskPollClock = {
    schedule(callback, delayMs) { const id = next++; scheduled.set(id, { callback, delayMs }); return id; },
    cancel(handle) { scheduled.delete(handle); },
  };
  const fireNext = () => {
    const first = scheduled.entries().next().value;
    assert.ok(first);
    scheduled.delete(first[0]);
    first[1].callback();
  };
  return { clock, scheduled, fireNext };
}

async function flush() { await Promise.resolve(); await Promise.resolve(); }

test("task refresh remains fast while any task is pending or running", () => {
  assert.equal(taskRefreshDelay([{ status: "success" }, { status: "pending" }]), ACTIVE_TASK_REFRESH_MS);
  assert.equal(taskRefreshDelay([{ status: "running" }]), ACTIVE_TASK_REFRESH_MS);
});

test("finished, empty and failed loads use slower refresh", () => {
  assert.equal(taskRefreshDelay([{ status: "success" }, { status: "failed" }]), IDLE_TASK_REFRESH_MS);
  assert.equal(taskRefreshDelay([]), IDLE_TASK_REFRESH_MS);
  assert.equal(taskRefreshDelay(null), IDLE_TASK_REFRESH_MS);
});

test("poller schedules only after each load settles and switches from active to idle", async () => {
  const { clock, scheduled, fireNext } = fakeClock();
  const releases: ((value: { status: string }[]) => void)[] = [];
  let loads = 0;
  let settled = 0;
  const stop = startTaskPolling(
    () => { loads++; return new Promise(resolve => { releases.push(resolve); }); },
    () => assert.fail("unexpected poll error"),
    () => { settled++; },
    clock,
  );
  assert.equal(loads, 1);
  assert.equal(scheduled.size, 0);
  releases[0]([{ status: "running" }]);
  await flush();
  assert.equal(settled, 1);
  assert.equal([...scheduled.values()][0].delayMs, ACTIVE_TASK_REFRESH_MS);
  fireNext();
  assert.equal(loads, 2);
  assert.equal(scheduled.size, 0);
  releases[1]([{ status: "success" }]);
  await flush();
  assert.equal(settled, 2);
  assert.equal([...scheduled.values()][0].delayMs, IDLE_TASK_REFRESH_MS);
  stop();
  assert.equal(scheduled.size, 0);
});

test("poller backs off after an error and suppresses late work after stop", async () => {
  const { clock, scheduled } = fakeClock();
  const errors: string[] = [];
  const stop = startTaskPolling(async () => { throw new Error("network down"); }, error => errors.push(String(error)), undefined, clock);
  await flush();
  assert.equal(errors.length, 1);
  assert.equal([...scheduled.values()][0].delayMs, IDLE_TASK_REFRESH_MS);
  stop();
  assert.equal(scheduled.size, 0);

  let release!: (value: { status: string }[]) => void;
  let settled = 0;
  const stopPending = startTaskPolling(() => new Promise(resolve => { release = resolve; }), () => assert.fail("unexpected error"), () => { settled++; }, clock);
  stopPending();
  release([{ status: "running" }]);
  await flush();
  assert.equal(settled, 0);
  assert.equal(scheduled.size, 0);

  let rejectLate!: (reason: Error) => void;
  const lateErrors: string[] = [];
  const stopRejected = startTaskPolling(() => new Promise((_, reject) => { rejectLate = reject; }), error => lateErrors.push(String(error)), undefined, clock);
  stopRejected();
  rejectLate(new Error("late network failure"));
  await flush();
  assert.deepEqual(lateErrors, []);
  assert.equal(scheduled.size, 0);
});
