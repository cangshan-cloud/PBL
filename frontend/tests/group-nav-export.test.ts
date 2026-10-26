import assert from "node:assert/strict";
import test from "node:test";
import { groupNavCsv, groupNavFilename } from "../src/group-nav-export.ts";

test("group NAV CSV retains stored group and date order, values and full Run ID", () => {
  const runId = "858c2667-19b8-4538-a02b-a3a16175adf5";
  const csv = groupNavCsv(runId, [
    { group: 1, points: [{ date: "2024-01-02", nav: 0.987654321 }, { date: "2024-01-03", nav: 1.01 }] },
    { group: 2, points: [{ date: "2024-01-02", nav: 1.02 }] },
  ]);
  assert.equal(groupNavFilename(runId), "group-nav-858c2667.csv");
  assert.deepEqual(csv.slice(1).trimEnd().split("\r\n"), [
    "run_id,group,date,nav",
    `${runId},1,2024-01-02,0.987654321`,
    `${runId},1,2024-01-03,1.01`,
    `${runId},2,2024-01-02,1.02`,
  ]);
  assert.equal(csv.charCodeAt(0), 0xFEFF);
});

test("group NAV CSV stays header-only when no group has points", () => {
  assert.equal(groupNavCsv("run-1", [{ group: 1, points: [] }, { group: 2, points: [] }]),
    "\uFEFFrun_id,group,date,nav\r\n");
});

test("group NAV CSV protects unexpected text without altering signed numbers", () => {
  const csv = groupNavCsv("=FORMULA()", [{ group: 1, points: [{ date: '+SUM(1),"quoted"', nav: -0.1 }] }]);
  assert.match(csv, /'=FORMULA\(\)/);
  assert.match(csv, /"'\+SUM\(1\),""quoted"""/);
  assert.match(csv, /,-0\.1\r\n/);
});
