import assert from "node:assert/strict";
import test from "node:test";
import { downloadDisclosedReport } from "../src/report-download.ts";

test("report delivery download uses selected Run and only confirms dispatch", async () => {
  const paths: string[] = [];
  const saved: string[] = [];
  const blob = new Blob(["<html>report</html>"], { type: "text/html; charset=utf-8" });
  const filename = await downloadDisclosedReport("12345678-aaaa", async path => {
    paths.push(path);
    return { ok: true, blob: async () => blob };
  }, (actual, name) => {
    assert.equal(actual, blob);
    saved.push(name);
  });
  assert.deepEqual(paths, ["/reports/12345678-aaaa/delivery"]);
  assert.deepEqual(saved, ["factor-report-12345678-disclosed.html"]);
  assert.equal(filename, saved[0]);
});

test("failed response or save never reports a completed download", async () => {
  let saved = false;
  await assert.rejects(downloadDisclosedReport("run", async () => ({ ok: false, blob: async () => new Blob() }),
    () => { saved = true; }), /请求失败/);
  assert.equal(saved, false);
  await assert.rejects(downloadDisclosedReport("run", async () => ({ ok: true, blob: async () => new Blob(["<html></html>"], { type: "text/html" }) }),
    () => { throw new Error("browser blocked download"); }), /browser blocked download/);
});

test("HTTP success with empty or non-HTML body is rejected before saving", async () => {
  let saved = false;
  for (const blob of [
    new Blob([], { type: "text/html" }),
    new Blob(['{"detail":"unexpected"}'], { type: "application/json" }),
    new Blob(["<html>report</html>"]),
  ]) {
    await assert.rejects(downloadDisclosedReport("run", async () => ({ ok: true, blob: async () => blob }),
      () => { saved = true; }), /非空 HTML/);
  }
  assert.equal(saved, false);
});
