import assert from "node:assert/strict";
import test from "node:test";
import { comparisonDownloadFilename, comparisonJsonContent } from "../src/comparison-download.ts";

test("comparison filename identifies selected runs in baseline order", () => {
  const ids = ["aaaaaaaa-1111-1111-1111-111111111111", "bbbbbbbb-2222-2222-2222-222222222222"];
  assert.equal(comparisonDownloadFilename("csv", ids), "factorlab-comparison-aaaaaaaa-bbbbbbbb.csv");
  assert.equal(comparisonDownloadFilename("html", [...ids].reverse()), "factorlab-comparison-bbbbbbbb-aaaaaaaa.html");
  assert.equal(comparisonDownloadFilename("json", ids), "factorlab-comparison-aaaaaaaa-bbbbbbbb.json");
});

test("comparison JSON preserves the displayed structured result", () => {
  const comparison = { items: [{ run_id: "run-a", metrics: { ic_mean: 0.12 } }], warnings: ["口径不同"] };
  const content = comparisonJsonContent(comparison);
  assert.ok(content.endsWith("\n"));
  assert.deepEqual(JSON.parse(content), {
    ...comparison,
    export_format: "factorlab-comparison",
    export_schema_version: 1,
  });
  assert.deepEqual(comparison, { items: [{ run_id: "run-a", metrics: { ic_mean: 0.12 } }], warnings: ["口径不同"] });
});

test("different comparison sets receive different filenames", () => {
  const first = comparisonDownloadFilename("csv", ["11111111-a", "22222222-b"]);
  const second = comparisonDownloadFilename("csv", ["11111111-a", "33333333-c"]);
  assert.notEqual(first, second);
});
