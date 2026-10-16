import assert from "node:assert/strict";
import test from "node:test";
import { forSelectedId } from "../src/selected-resource.ts";

test("selected resource is visible only for its matching task or report", () => {
  const resource = { id: "run-a", value: "report-a" };
  assert.equal(forSelectedId(resource, "run-a"), "report-a");
  assert.equal(forSelectedId(resource, "run-b"), null);
  assert.equal(forSelectedId(resource, undefined), null);
  assert.equal(forSelectedId(null, "run-a"), null);
});
