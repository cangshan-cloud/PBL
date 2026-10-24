import assert from "node:assert/strict";
import test from "node:test";
import { saveBlobAsFile, type DownloadPort } from "../src/blob-download.ts";

function fakePort(failClick = false) {
  const events: string[] = [];
  let release: (() => void) | undefined;
  const anchor = {
    href: "",
    download: "",
    click() { events.push("click"); if (failClick) throw new Error("click failed"); },
    remove() { events.push("remove"); },
  };
  const port: DownloadPort = {
    createAnchor: () => anchor,
    attach: () => { events.push("attach"); },
    createObjectURL: () => "blob:test",
    revokeObjectURL: url => { events.push(`revoke:${url}`); },
    defer: (callback, delayMs) => { assert.equal(delayMs, 30_000); release = callback; },
  };
  return { port, anchor, events, release: () => release?.() };
}

test("download keeps Blob URL alive until deferred release", () => {
  const fixture = fakePort();
  saveBlobAsFile(new Blob(["data"]), "factor.csv", fixture.port);
  assert.equal(fixture.anchor.href, "blob:test");
  assert.equal(fixture.anchor.download, "factor.csv");
  assert.deepEqual(fixture.events, ["attach", "click", "remove"]);
  fixture.release();
  assert.deepEqual(fixture.events, ["attach", "click", "remove", "revoke:blob:test"]);
});

test("failed click still removes anchor and schedules URL release", () => {
  const fixture = fakePort(true);
  assert.throws(() => saveBlobAsFile(new Blob(), "failed.html", fixture.port), /click failed/);
  assert.deepEqual(fixture.events, ["attach", "click", "remove"]);
  fixture.release();
  assert.equal(fixture.events.at(-1), "revoke:blob:test");
});
