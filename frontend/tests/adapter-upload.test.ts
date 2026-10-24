import assert from "node:assert/strict";
import test from "node:test";
import { prepareAdapterImportBody } from "../src/adapter-upload.ts";

const digest = "a".repeat(64);

test("adapted import binds the previewed source digest", () => {
  const body = new FormData();
  body.set("normalize_cn_csv", "true");
  body.set("expected_source_sha256", "stale");
  assert.equal(prepareAdapterImportBody(body, { source_sha256: digest }).get("expected_source_sha256"), digest);
});

test("direct and standard imports do not inherit a preview digest", () => {
  const direct = new FormData();
  direct.set("normalize_cn_csv", "true");
  assert.equal(prepareAdapterImportBody(direct, null).has("expected_source_sha256"), false);

  const standard = new FormData();
  standard.set("normalize_cn_csv", "false");
  standard.set("expected_source_sha256", "stale");
  assert.equal(prepareAdapterImportBody(standard, { source_sha256: digest }).has("expected_source_sha256"), false);
});

test("an invalid preview digest cannot silently downgrade to an unbound adapted import", () => {
  const body = new FormData();
  body.set("normalize_cn_csv", "true");
  assert.throws(() => prepareAdapterImportBody(body, { source_sha256: "missing" }), /重新预览/);
  assert.equal(body.has("expected_source_sha256"), false);
});

test("changing a previewed file requires another preview before adapted import", () => {
  const adapted = new FormData();
  adapted.set("normalize_cn_csv", "true");
  assert.throws(() => prepareAdapterImportBody(adapted, null, true), /文件已更换.*重新预览/);
  const standard = new FormData();
  standard.set("normalize_cn_csv", "false");
  assert.equal(prepareAdapterImportBody(standard, null, true).has("expected_source_sha256"), false);
});
