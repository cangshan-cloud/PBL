import assert from "node:assert/strict";
import test from "node:test";
import { adapterCalendarDetails, calendarDatasetAlerts, importedCsvProvenanceNotice, isKnownSyntheticDemo, reportCalendarRiskNotice, reportDatasetByIdentity, selectedWeekendDatasetAlert, weekendDatasetAlerts } from "../src/dataset-alerts.ts";

test("weekend alerts include only versions with affected rows", () => {
  const datasets = [
    { id: "old", name: "旧版", dataset_key: "prices", version: "v1", quality_report: {} },
    { id: "clean", name: "正常版", dataset_key: "prices", version: "v2", quality_report: { weekend_date_count: 0, weekend_row_count: 0 } },
    { id: "warn", name: "待复核", dataset_key: "prices", version: "v3", quality_report: { weekend_date_count: 1, weekend_row_count: 2 } },
  ];
  assert.deepEqual(weekendDatasetAlerts(datasets).map(item => item.id), ["warn"]);
  assert.equal(selectedWeekendDatasetAlert(datasets[0]), undefined);
  assert.equal(selectedWeekendDatasetAlert(datasets[1]), undefined);
  assert.equal(selectedWeekendDatasetAlert(datasets[2])?.id, "warn");
  assert.equal(selectedWeekendDatasetAlert(undefined), undefined);
});

test("calendar alerts distinguish announced closures, uncovered years, and legacy reports", () => {
  const datasets = [
    { id: "old", name: "旧版", dataset_key: "p", version: "v1", quality_report: {} },
    { id: "closed", name: "休市行", dataset_key: "p", version: "v2", quality_report: { announced_weekday_closure_row_count: 2 } },
    { id: "unknown", name: "范围外", dataset_key: "p", version: "v3", quality_report: { calendar_uncovered_years: [2026] } },
  ];
  assert.deepEqual(calendarDatasetAlerts(datasets).map(item => item.id), ["closed", "unknown"]);
});

test("synthetic demo disclosure is bound to the known immutable version", () => {
  const demo = { id: "x", name: "演示", dataset_key: "demo_daily", version: "0.2.0",
    checksum: "c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e", quality_report: {} };
  assert.equal(isKnownSyntheticDemo(demo), true);
  assert.equal(isKnownSyntheticDemo({ ...demo, checksum: "other" }), false);
  assert.equal(isKnownSyntheticDemo(undefined), false);
});

test("ordinary imported CSV provenance warning excludes demo, sealed bundle, and unknown legacy metadata", () => {
  const csv = { id: "csv", name: "导入", dataset_key: "prices", version: "v1",
    quality_report: { columns: ["trade_date", "symbol", "close"] } };
  assert.match(importedCsvProvenanceNotice(csv) ?? "", /不认证数据真实性、使用授权或完整交易日历/);
  assert.equal(importedCsvProvenanceNotice({ ...csv, quality_report: {} }), null);
  assert.equal(importedCsvProvenanceNotice({ ...csv,
    quality_report: { ...csv.quality_report, dataset_kind: "hs300_bundle_v1" } }), null);
  assert.equal(importedCsvProvenanceNotice({ ...csv, dataset_key: "demo_daily", version: "0.2.0",
    checksum: "c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e" }), null);
  assert.equal(importedCsvProvenanceNotice({ ...csv, dataset_key: "demo_daily",
    quality_report: { ...csv.quality_report, source: "bundled_demo" } }), null);
});

test("archived report joins dataset by both immutable id and checksum", () => {
  const dataset = { id: "v1", name: "演示", dataset_key: "demo_daily", version: "0.2.0", checksum: "sha", quality_report: {} };
  assert.equal(reportDatasetByIdentity([dataset], { dataset_version_id: "v1", dataset_checksum_sha256: "sha" }), dataset);
  assert.equal(reportDatasetByIdentity([dataset], { dataset_version_id: "v1", dataset_checksum_sha256: "other" }), undefined);
  assert.equal(reportDatasetByIdentity([dataset], { dataset_version_id: "other", dataset_checksum_sha256: "sha" }), undefined);
});

test("report calendar notice uses only the identity-matched version", () => {
  const dataset = { id: "v1", name: "导入", dataset_key: "prices", version: "v1", checksum: "sha",
    quality_report: { announced_weekday_closure_row_count: 3, announced_weekday_closure_dates: ["2026-10-07"],
      announced_closure_calendar_version: "calendar-v2", calendar_uncovered_years: [2027] } };
  const matched = reportDatasetByIdentity([dataset], { dataset_version_id: "v1", dataset_checksum_sha256: "sha" });
  assert.equal(reportCalendarRiskNotice(matched),
    "当前报告的数据版本公告休市核对：3 行行情命中（2026-10-07）；2027 年未覆盖；规则版本：calendar-v2。仅供人工复核，旧归档 HTML 未改写。");
  const mismatched = reportDatasetByIdentity([dataset], { dataset_version_id: "v1", dataset_checksum_sha256: "changed" });
  assert.equal(reportCalendarRiskNotice(mismatched), null);
  assert.equal(reportCalendarRiskNotice({ ...dataset, quality_report: {} }), null);
});

test("adapter preview names affected dates and sealed calendar version", () => {
  assert.equal(adapterCalendarDetails({ announced_weekday_closure_dates: ["2026-10-07"],
    announced_closure_calendar_version: "sse-szse-announced-closures-2024-2026-v2" }),
    "命中公告休市工作日：2026-10-07；规则版本：sse-szse-announced-closures-2024-2026-v2。仅供导入前人工复核，不自动删行。");
  assert.match(adapterCalendarDetails({ calendar_uncovered_years: [2027] }) ?? "", /未覆盖年份：2027/);
  assert.equal(adapterCalendarDetails({}), null);
});
