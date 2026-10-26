import assert from "node:assert/strict";
import test from "node:test";
import { loadForCurrentSession, loadForLatestRequest } from "../src/auth-resource.ts";

test("current account may publish loaded resources", async () => {
  const value = await loadForCurrentSession(async () => ["own-task"], 1, () => 1);
  assert.deepEqual(value, ["own-task"]);
});

test("logout discards a late resource response", async () => {
  let generation = 1;
  let release!: (value: string[]) => void;
  const response = new Promise<string[]>(resolve => { release = resolve; });
  const loading = loadForCurrentSession(() => response, 1, () => generation);
  generation = 2;
  release(["previous-account-task"]);
  assert.equal(await loading, null);
});

test("logout suppresses a late resource error", async () => {
  let generation = 1;
  let reject!: (reason: Error) => void;
  const response = new Promise<string[]>((_, fail) => { reject = fail; });
  const loading = loadForCurrentSession(() => response, 1, () => generation);
  generation = 2;
  reject(new Error("previous account request failed"));
  assert.equal(await loading, null);
});

test("current account still sees load errors", async () => {
  await assert.rejects(
    loadForCurrentSession(async () => { throw new Error("request failed"); }, 1, () => 1),
    /request failed/,
  );
});

test("older same-session response cannot replace a newer task list", async () => {
  let resolveOld!: (value: string[]) => void;
  const oldResponse = new Promise<string[]>(resolve => { resolveOld = resolve; });
  let request = 1;
  const oldLoad = loadForLatestRequest(() => oldResponse, 1, () => 1, 1, () => request);
  request = 2;
  const newLoad = loadForLatestRequest(async () => ["new-run"], 1, () => 1, 2, () => request);
  assert.deepEqual(await newLoad, ["new-run"]);
  resolveOld(["old-run"]);
  assert.equal(await oldLoad, null);
});

test("older same-session load failure is suppressed, current failure is surfaced", async () => {
  let rejectOld!: (reason: Error) => void;
  const oldResponse = new Promise<string[]>((_, reject) => { rejectOld = reject; });
  let request = 1;
  const oldLoad = loadForLatestRequest(() => oldResponse, 1, () => 1, 1, () => request);
  request = 2;
  rejectOld(new Error("stale error"));
  assert.equal(await oldLoad, null);
  await assert.rejects(loadForLatestRequest(async () => { throw new Error("current error"); }, 1, () => 1, 2, () => request), /current error/);
});
