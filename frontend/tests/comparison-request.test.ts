import assert from "node:assert/strict";
import test from "node:test";
import { resolveCurrentComparison } from "../src/comparison-request.ts";

test("current comparison response can be published", async () => {
  const result = await resolveCurrentComparison(async () => ({ runIds: ["a", "b"] }), () => true);
  assert.deepEqual(result, { runIds: ["a", "b"] });
});

test("selection changed before request starts skips network work", async () => {
  let requests = 0;
  const result = await resolveCurrentComparison(async () => { requests += 1; return "old"; }, () => false);
  assert.equal(result, null);
  assert.equal(requests, 0);
});

test("selection or login changed during request discards late response", async () => {
  let current = true;
  let release!: (value: string) => void;
  const response = new Promise<string>(resolve => { release = resolve; });
  const resultPromise = resolveCurrentComparison(() => response, () => current);
  current = false;
  release("old comparison");
  assert.equal(await resultPromise, null);
});
