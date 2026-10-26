"""Full HTTP journey using isolated SQLite and uploaded CSV, without Docker or network."""

import csv
import hashlib
import html
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from kombu.exceptions import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Artifact, DatasetVersion, Run, RunStatus, User
from app.services.runs import claim_pending_run, create_historical_run


SAMPLE_CSV = Path(__file__).resolve().parents[2] / "data" / "sample" / "daily_prices.csv"


class ApiJourneyTests(unittest.TestCase):
    def test_predeclared_time_split_survives_task_report_and_conclusion(self):
        researcher = self.auth("researcher", "research12345")
        base = {"factor": "momentum_20d", "groups": 5,
                "start_date": "2025-02-03", "end_date": "2025-05-30"}
        original = self.client.post("/api/v1/research/tasks", headers=researcher, json=base)
        split = self.client.post("/api/v1/research/tasks", headers=researcher,
                                 json={**base, "validation_start_date": "2025-04-01"})
        self.assertEqual(original.status_code, 201, original.text)
        self.assertEqual(split.status_code, 201, split.text)
        baseline = original.json()["result"]
        result = split.json()["result"]
        self.assertEqual(result["coverage"], baseline["coverage"])
        self.assertEqual(result["ic_mean"], baseline["ic_mean"])
        self.assertEqual(result["time_split"]["validation_start_date"], "2025-04-01")
        self.assertLess(result["time_split"]["research"]["end_date"],
                        result["time_split"]["validation"]["start_date"])
        run_id = split.json()["id"]
        report = self.client.get(f"/api/v1/reports/{run_id}/html", headers=researcher)
        self.assertEqual(report.status_code, 200, report.text)
        self.assertIn("时间切分 IC 诊断", report.text)
        conclusion = self.client.get(f"/api/v1/research/tasks/{run_id}/conclusion", headers=researcher)
        self.assertEqual(conclusion.status_code, 200, conclusion.text)
        self.assertTrue(any("验证期始于" in item for item in conclusion.json()["evidence"]))
        self.assertEqual(conclusion.json()["method"]["grade_basis"], "validation_ic")
        self.assertNotEqual(conclusion.json()["grade"], "promising")

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )

        def isolated_db():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_db] = isolated_db
        self.env = patch.dict(os.environ, {
            "DATA_ROOT": self.temp_dir.name,
            "TASK_EXECUTION_MODE": "inline",
            "JWT_SECRET": "isolated-api-journey-test-secret",
        })
        self.env.start()
        self.engine_patch = patch("app.main.engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        app.dependency_overrides.clear()
        self.engine_patch.stop()
        self.env.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def auth(self, username: str, password: str) -> dict[str, str]:
        response = self.client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_missing_adjustment_column_is_rejected_before_run_creation(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        rows = ["trade_date,symbol,close,pe"]
        for index, day in enumerate(("2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07")):
            for ordinal, symbol in enumerate(("000001.SZ", "000002.SZ", "000003.SZ"), start=1):
                rows.append(f"{day},{symbol},{10 + index + ordinal},{ordinal * 3 + index}")
        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "no_multiplier_journey", "name": "无复权乘数隔离样本"},
            files={"file": ("no-multiplier.csv", ("\n".join(rows) + "\n").encode(), "text/csv")},
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertNotIn("adj_factor", dataset["quality_report"]["columns"])
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset['id']}/publish", headers=admin).status_code, 200)
        before = len(self.client.get("/api/v1/research/tasks", headers=researcher).json())
        for endpoint, payload in (
            ("/api/v1/research/tasks", {"factor": "pe"}),
            ("/api/v1/research/composite-tasks", {"factors": ["pe", "momentum_20d"]}),
        ):
            rejected = self.client.post(endpoint, headers=researcher, json={
                "dataset_version_id": dataset["id"], "price_basis": "factor_adjusted", "groups": 2, **payload,
            })
            self.assertEqual(rejected.status_code, 400, rejected.text)
            self.assertIn("missing adj_factor", rejected.json()["detail"])
        self.assertEqual(len(self.client.get("/api/v1/research/tasks", headers=researcher).json()), before)

    def test_missing_adjustment_values_reject_full_sample_but_not_valid_symbol_subset(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        rows = ["trade_date,symbol,close,pe,adj_factor"]
        for index, day in enumerate(("2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07")):
            for ordinal, symbol in enumerate(("000001.SZ", "000002.SZ", "000003.SZ"), start=1):
                factor = "" if index == 1 and ordinal == 2 else "1"
                rows.append(f"{day},{symbol},{10 + index + ordinal},{ordinal * 3 + index},{factor}")
        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "partial_multiplier_journey", "name": "部分缺乘数隔离样本"},
            files={"file": ("partial-multiplier.csv", ("\n".join(rows) + "\n").encode(), "text/csv")},
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertEqual(dataset["quality_report"]["missing_counts"]["adj_factor"], 1)
        self.assertEqual(dataset["quality_report"]["missing_adj_factor_by_symbol"], {"000002.SZ": 1})
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset['id']}/publish", headers=admin).status_code, 200)
        before = len(self.client.get("/api/v1/research/tasks", headers=researcher).json())
        for endpoint, payload in (
            ("/api/v1/research/tasks", {"factor": "pe"}),
            ("/api/v1/research/composite-tasks", {"factors": ["pe", "momentum_20d"]}),
        ):
            rejected = self.client.post(endpoint, headers=researcher, json={
                "dataset_version_id": dataset["id"], "price_basis": "factor_adjusted", "groups": 2, **payload,
            })
            self.assertEqual(rejected.status_code, 400, rejected.text)
            self.assertIn("missing adj_factor values", rejected.json()["detail"])
        self.assertEqual(len(self.client.get("/api/v1/research/tasks", headers=researcher).json()), before)
        affected = self.client.post("/api/v1/research/tasks", headers=researcher, json={
            "dataset_version_id": dataset["id"], "price_basis": "factor_adjusted", "factor": "pe",
            "groups": 2, "symbols": ["000001.SZ", "000002.SZ"],
        })
        self.assertEqual(affected.status_code, 400, affected.text)
        self.assertIn("selected symbols have missing", affected.json()["detail"])
        self.assertEqual(len(self.client.get("/api/v1/research/tasks", headers=researcher).json()), before)
        selected = self.client.post("/api/v1/research/tasks", headers=researcher, json={
            "dataset_version_id": dataset["id"], "price_basis": "factor_adjusted", "factor": "pe",
            "groups": 2, "symbols": ["000001.SZ", "000003.SZ"],
        })
        self.assertEqual(selected.status_code, 201, selected.text)
        self.assertEqual(selected.json()["status"], "success", selected.text)
        run_id = selected.json()["id"]
        archived = self.client.get(f"/api/v1/reports/{run_id}/download", headers=researcher)
        self.assertEqual(archived.status_code, 200, archived.text)
        self.assertIn("全量质量报告有 1 行缺失 adj_factor", archived.text)
        self.assertIn("不代表版本内其他证券可用于调整价研究", archived.text)
        self.assertIn("不认证数据真实性、使用授权或完整交易日历", archived.text)
        archive_sha = hashlib.sha256(archived.content).hexdigest()
        delivery = self.client.get(f"/api/v1/reports/{run_id}/delivery", headers=researcher)
        self.assertEqual(delivery.status_code, 200, delivery.text)
        self.assertEqual(delivery.text.count("全量质量报告有 1 行缺失 adj_factor"), 2)
        self.assertEqual(delivery.text.count("不认证数据真实性、使用授权或完整交易日历"), 2)
        self.assertEqual(delivery.headers["x-archived-report-sha256"], archive_sha)
        self.assertEqual(self.client.get(f"/api/v1/reports/{run_id}/download", headers=researcher).content,
                         archived.content)
        source_close = self.client.post("/api/v1/research/tasks", headers=researcher, json={
            "dataset_version_id": dataset["id"], "price_basis": "source_close", "factor": "pe",
            "groups": 2, "symbols": ["000001.SZ", "000003.SZ"],
        })
        self.assertEqual(source_close.status_code, 201, source_close.text)
        self.assertEqual(source_close.json()["status"], "success", source_close.text)
        close_report = self.client.get(
            f"/api/v1/reports/{source_close.json()['id']}/download", headers=researcher,
        )
        self.assertEqual(close_report.status_code, 200, close_report.text)
        self.assertNotIn("全量质量报告有 1 行缺失 adj_factor", close_report.text)
        self.assertIn("不认证数据真实性、使用授权或完整交易日历", close_report.text)

    def test_weekend_diagnostic_matches_adapter_preview_and_import(self):
        admin = self.auth("admin", "admin12345")
        source = b"date,code,close\n20250104,000001,10\n20250104,600000,11\n20250106,000001,12\n"
        upload = {"file": ("weekend.csv", source, "text/csv")}
        preview = self.client.post("/api/v1/datasets/adapt/preview", headers=admin, files=upload)
        self.assertEqual(preview.status_code, 200, preview.text)
        report = preview.json()["report"]
        source_sha256 = preview.json()["source_sha256"]
        self.assertEqual(source_sha256, hashlib.sha256(source).hexdigest())
        self.assertEqual(report["validation"]["weekend_date_count"], 1)
        self.assertEqual(report["validation"]["weekend_row_count"], 2)
        self.assertTrue(any("导入前核对" in warning for warning in report["warnings"]))

        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "weekend_check", "name": "周末日期隔离样本", "normalize_cn_csv": "true",
                  "expected_source_sha256": source_sha256},
            files=upload,
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertEqual(dataset["row_count"], 3)
        self.assertNotEqual(dataset["checksum"], source_sha256)
        self.assertEqual(dataset["quality_report"]["weekend_date_count"], 1)
        self.assertEqual(dataset["quality_report"]["weekend_row_count"], 2)
        self.assertEqual(dataset["quality_report"]["adapter_report"]["validation"], report["validation"])

    def test_announced_closure_preview_and_import_share_diagnostic(self):
        admin = self.auth("admin", "admin12345")
        source = b"date,code,close\n20250128,000001,10\n20250128,600000,11\n20250205,000001,12\n"
        upload = {"file": ("closure.csv", source, "text/csv")}
        preview = self.client.post("/api/v1/datasets/adapt/preview", headers=admin, files=upload)
        self.assertEqual(preview.status_code, 200, preview.text)
        validation = preview.json()["report"]["validation"]
        self.assertEqual(validation["announced_weekday_closure_date_count"], 1)
        self.assertEqual(validation["announced_weekday_closure_row_count"], 2)
        self.assertTrue(any("公告休市工作日" in warning for warning in preview.json()["report"]["warnings"]))
        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "closure_check", "name": "公告休市隔离样本", "normalize_cn_csv": "true",
                  "expected_source_sha256": preview.json()["source_sha256"]},
            files=upload,
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertEqual(dataset["row_count"], 3)
        self.assertEqual(dataset["quality_report"]["announced_weekday_closure_dates"], ["2025-01-28"])
        self.assertEqual(dataset["quality_report"]["announced_weekday_closure_row_count"], 2)
        self.assertEqual(dataset["quality_report"]["adapter_report"]["validation"], validation)

    def test_calendar_risk_survives_import_run_and_report_delivery(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        rows = ["date,code,close,pe"]
        for index, day in enumerate(("20261007", "20261008", "20261009", "20270104")):
            for ordinal, symbol in enumerate(("000001", "000002", "000003"), start=1):
                rows.append(f"{day},{symbol},{10 + index + ordinal},{ordinal * 3 + index}")
        source = ("\n".join(rows) + "\n").encode()
        upload = {"file": ("calendar-risk.csv", source, "text/csv")}

        preview = self.client.post("/api/v1/datasets/adapt/preview", headers=admin, files=upload)
        self.assertEqual(preview.status_code, 200, preview.text)
        validation = preview.json()["report"]["validation"]
        self.assertEqual(validation["announced_weekday_closure_dates"], ["2026-10-07"])
        self.assertEqual(validation["calendar_uncovered_years"], [2027])

        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "calendar_report_journey", "name": "日历风险报告隔离样本",
                  "normalize_cn_csv": "true", "expected_source_sha256": preview.json()["source_sha256"]},
            files=upload,
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertEqual(dataset["quality_report"]["announced_weekday_closure_row_count"], 3)
        self.assertEqual(dataset["quality_report"]["calendar_uncovered_years"], [2027])
        published = self.client.post(f"/api/v1/datasets/{dataset['id']}/publish", headers=admin)
        self.assertEqual(published.status_code, 200, published.text)

        created = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset["id"], "factor": "pe", "groups": 2},
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["status"], "success")
        run_id = created.json()["id"]
        indexed = self.client.get("/api/v1/reports", headers=researcher)
        self.assertEqual(indexed.status_code, 200, indexed.text)
        listed = next(item for item in indexed.json() if item["run_id"] == run_id)
        self.assertEqual(listed["dataset_version_id"], dataset["id"])
        self.assertEqual(listed["dataset_checksum_sha256"], dataset["checksum"])

        archived = self.client.get(f"/api/v1/reports/{run_id}/download", headers=researcher)
        self.assertEqual(archived.status_code, 200, archived.text)
        archive_sha = hashlib.sha256(archived.content).hexdigest()
        self.assertEqual(archive_sha, listed["checksum"])
        for expected in ("3 行沪深交易所公告休市工作日行情", "2026-10-07", "未覆盖 2027 年"):
            self.assertIn(expected, archived.text)

        delivery = self.client.get(f"/api/v1/reports/{run_id}/delivery", headers=researcher)
        self.assertEqual(delivery.status_code, 200, delivery.text)
        self.assertIn("交付披露副本 · 非原始归档字节", delivery.text)
        self.assertIn(dataset["checksum"], delivery.text)
        self.assertIn(archive_sha, delivery.text)
        self.assertEqual(delivery.headers["x-archived-report-sha256"], archive_sha)
        for expected in ("3 行沪深交易所公告休市工作日行情", "2026-10-07", "未覆盖 2027 年"):
            self.assertIn(expected, delivery.text)
        again = self.client.get(f"/api/v1/reports/{run_id}/download", headers=researcher)
        self.assertEqual(again.content, archived.content)

    def test_adapter_price_status_survives_import_run_and_report_delivery(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        rows = ["date,code,close,pe,adjustflag"]
        for index, day in enumerate(("20250102", "20250103", "20250106", "20250107")):
            for ordinal, symbol in enumerate(("000001", "000002", "000003"), start=1):
                rows.append(f"{day},{symbol},{10 + index + ordinal},{ordinal * 3 + index},2")
        source = ("\n".join(rows) + "\n").encode()
        upload = {"file": ("adjusted.csv", source, "text/csv")}
        preview = self.client.post("/api/v1/datasets/adapt/preview", headers=admin, files=upload)
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.json()["report"]["source_adjustment_flags"], ["2"])
        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "adjusted_status_journey", "name": "复权状态隔离样本",
                  "normalize_cn_csv": "true", "expected_source_sha256": preview.json()["source_sha256"]},
            files=upload,
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertEqual(dataset["quality_report"]["adapter_report"]["source_adjustment_flags"], ["2"])
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset['id']}/publish", headers=admin).status_code, 200)

        before = len(self.client.get("/api/v1/research/tasks", headers=researcher).json())
        for endpoint, payload in (
            ("/api/v1/research/tasks", {"factor": "pe"}),
            ("/api/v1/research/composite-tasks", {"factors": ["pe", "momentum_20d"]}),
        ):
            rejected = self.client.post(endpoint, headers=researcher, json={
                "dataset_version_id": dataset["id"], "price_basis": "factor_adjusted", "groups": 2, **payload,
            })
            self.assertEqual(rejected.status_code, 400, rejected.text)
            self.assertIn("double adjustment", rejected.json()["detail"])
        self.assertEqual(len(self.client.get("/api/v1/research/tasks", headers=researcher).json()), before)

        created = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset["id"], "factor": "pe", "groups": 2},
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["status"], "success")
        run_id = created.json()["id"]
        indexed = self.client.get("/api/v1/reports", headers=researcher)
        self.assertEqual(indexed.status_code, 200, indexed.text)
        summary = next(item for item in indexed.json() if item["run_id"] == run_id)
        self.assertEqual(summary["dataset_version_id"], dataset["id"])
        self.assertEqual(summary["dataset_checksum_sha256"], dataset["checksum"])

        archived = self.client.get(f"/api/v1/reports/{run_id}/download", headers=researcher)
        self.assertEqual(archived.status_code, 200, archived.text)
        archive_sha = hashlib.sha256(archived.content).hexdigest()
        self.assertEqual(archive_sha, summary["checksum"])
        self.assertIn("adjustflag=2（来源声明的前复权状态）", archived.text)
        self.assertIn("价格口径：导入的 close", archived.text)
        delivery = self.client.get(f"/api/v1/reports/{run_id}/delivery", headers=researcher)
        self.assertEqual(delivery.status_code, 200, delivery.text)
        self.assertEqual(delivery.text.count("adjustflag=2"), 2)
        self.assertEqual(delivery.headers["x-archived-report-sha256"], archive_sha)
        self.assertIn(dataset["checksum"], delivery.text)
        self.assertEqual(self.client.get(f"/api/v1/reports/{run_id}/download", headers=researcher).content,
                         archived.content)

    def test_adapter_import_rejects_changed_file_after_preview_without_creating_draft(self):
        admin = self.auth("admin", "admin12345")
        original = b"date,code,close\n20250104,000001,10\n"
        altered = b"date,code,close\n20250104,000001,11\n"
        preview = self.client.post(
            "/api/v1/datasets/adapt/preview", headers=admin,
            files={"file": ("data.csv", original, "text/csv")},
        )
        self.assertEqual(preview.status_code, 200, preview.text)
        fields = {"dataset_key": "preview_changed", "name": "预览后变化",
                  "normalize_cn_csv": "true", "expected_source_sha256": preview.json()["source_sha256"]}
        rejected = self.client.post(
            "/api/v1/datasets/import", headers=admin, data=fields,
            files={"file": ("data.csv", altered, "text/csv")},
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)
        self.assertIn("重新预览", rejected.json()["detail"])
        self.assertFalse(any(item["dataset_key"] == "preview_changed" for item in
                             self.client.get("/api/v1/datasets", headers=admin).json()))
        malformed = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={**fields, "expected_source_sha256": "bad"},
            files={"file": ("data.csv", original, "text/csv")},
        )
        self.assertEqual(malformed.status_code, 400, malformed.text)

    def test_default_loopback_frontends_can_preflight_login(self):
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            with self.subTest(origin=origin):
                response = self.client.options(
                    "/api/v1/auth/login",
                    headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                             "Access-Control-Request-Headers": "content-type"},
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.headers.get("access-control-allow-origin"), origin)

        rejected = self.client.options(
            "/api/v1/auth/login",
            headers={"Origin": "http://localhost.evil.example:5173", "Access-Control-Request-Method": "POST"},
        )
        self.assertNotEqual(rejected.headers.get("access-control-allow-origin"), "http://localhost.evil.example:5173")

    def test_publish_blocks_tampered_or_missing_draft(self):
        admin = self.auth("admin", "admin12345")
        original = b"trade_date,symbol,close\n2025-01-02,000001.SZ,10\n"
        response = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "tamper_test", "name": "完整性测试"},
            files={"file": ("daily.csv", original, "text/csv")},
        )
        self.assertEqual(response.status_code, 201, response.text)
        dataset_id = response.json()["id"]
        with Session(self.engine) as session:
            path = Path(session.get(DatasetVersion, dataset_id).storage_uri)

        path.write_bytes(original.replace(b",10\n", b",11\n"))
        publish_url = f"/api/v1/datasets/{dataset_id}/publish"
        self.assertEqual(self.client.post(publish_url, headers=admin).status_code, 409)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}", headers=admin).json()["status"], "draft")

        path.unlink()
        self.assertEqual(self.client.post(publish_url, headers=admin).status_code, 410)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}", headers=admin).json()["status"], "draft")

        path.write_bytes(original)
        self.assertEqual(self.client.post(publish_url, headers=admin).status_code, 200)

    def test_selected_symbols_keep_full_dataset_market_calendar(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        lines = ["trade_date,symbol,close,pe"]
        for index in range(7):
            for symbol in ("A", "B", "C"):
                if index == 2 and symbol in {"A", "B"}:
                    continue
                lines.append(f"2025-01-{index + 1:02d},{symbol},{10 + index},{8 + index}")
        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "calendar_gap", "name": "日历缺行样本"},
            files={"file": ("prices.csv", ("\n".join(lines) + "\n").encode(), "text/csv")},
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset_id = imported.json()["id"]
        self.assertEqual(imported.json()["quality_report"]["internal_calendar_gap_count"], 2)
        published = self.client.post(f"/api/v1/datasets/{dataset_id}/publish", headers=admin)
        self.assertEqual(published.status_code, 200, published.text)
        created = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset_id, "factor": "pe", "groups": 2, "symbols": ["A", "B"]},
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["status"], "success")
        self.assertEqual(created.json()["result"]["coverage"], 8)
        daily = {item["date"]: item for item in created.json()["result"]["daily_coverage"]}
        self.assertEqual(daily["2025-01-02"]["candidate_symbols"], 2)
        self.assertEqual(daily["2025-01-02"]["eligible_symbols"], 0)
        self.assertEqual(daily["2025-01-02"]["coverage_ratio"], 0)
        self.assertEqual(daily["2025-01-03"]["candidate_symbols"], 0)
        self.assertEqual(daily["2025-01-03"]["ic_status"], "no_observation")
        self.assertIsNone(daily["2025-01-03"]["coverage_ratio"])

    def test_sparse_factor_dates_are_disclosed_across_task_conclusion_and_report(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        lines = ["trade_date,symbol,close,pe"]
        for index in range(5):
            for symbol, base, ordinal in (("A", 10, 1), ("B", 20, 2), ("C", 30, 3)):
                if index == 2 and symbol == "C":
                    continue
                pe = 1 if index == 0 else ordinal
                lines.append(f"2025-01-{index + 1:02d},{symbol},{base + index},{pe}")
        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "sparse_factor_days", "name": "稀疏截面验收"},
            files={"file": ("prices.csv", ("\n".join(lines) + "\n").encode(), "text/csv")},
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset_id = imported.json()["id"]
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/publish", headers=admin).status_code, 200)

        created = self.client.post("/api/v1/research/tasks", headers=researcher,
                                   json={"dataset_version_id": dataset_id, "factor": "pe", "groups": 3})
        self.assertEqual(created.status_code, 201, created.text)
        task = created.json()
        self.assertEqual(task["status"], "success")
        result = task["result"]
        self.assertEqual(result["coverage"], 10)
        self.assertEqual(result["group_skipped_constant_factor_days"], 1)
        self.assertEqual(result["group_skipped_insufficient_sample_days"], 2)
        self.assertEqual(result["zero_observation_days"], 1)
        self.assertEqual(result["daily_coverage"][-1]["eligible_symbols"], 0)
        self.assertEqual([item["date"] for item in result["long_short_series"]], ["2025-01-04"])
        self.assertIsNone(result["ic_series"][0]["ic"])
        snapshot = self.client.get(f"/api/v1/research/tasks/{task['id']}/reproducibility.json", headers=researcher)
        self.assertEqual(snapshot.status_code, 200, snapshot.text)
        self.assertEqual(snapshot.json()["result"]["group_skipped_constant_factor_days"], 1)
        self.assertEqual(snapshot.json()["result"]["group_skipped_insufficient_sample_days"], 2)

        conclusion = self.client.get(f"/api/v1/research/tasks/{task['id']}/conclusion", headers=researcher)
        self.assertEqual(conclusion.status_code, 200, conclusion.text)
        self.assertTrue(any("全截面因子同值" in item for item in conclusion.json()["limitations"]))
        self.assertTrue(any("有效证券数少于目标分组数" in item for item in conclusion.json()["limitations"]))
        self.assertTrue(any("未形成任何有效因子" in item for item in conclusion.json()["limitations"]))
        report = self.client.get(f"/api/v1/reports/{task['id']}/html", headers=researcher)
        self.assertEqual(report.status_code, 200, report.text)
        self.assertIn("全截面因子同值而跳过分组的日期：1 天", report.text)
        self.assertIn("有效证券数少于目标分组数而跳过的日期：2 天", report.text)

        sparse_only = self.client.post("/api/v1/research/tasks", headers=researcher,
                                       json={"dataset_version_id": dataset_id, "factor": "pe", "groups": 3,
                                             "end_date": "2025-01-03"})
        self.assertEqual(sparse_only.status_code, 201, sparse_only.text)
        self.assertEqual(sparse_only.json()["status"], "success")
        sparse_result = sparse_only.json()["result"]
        self.assertEqual(sparse_result["group_returns"], [])
        self.assertEqual(sparse_result["long_short_series"], [])
        self.assertIsNone(sparse_result["long_short_total_return"])
        sparse_conclusion = self.client.get(f"/api/v1/research/tasks/{sparse_only.json()['id']}/conclusion",
                                            headers=researcher)
        self.assertEqual(sparse_conclusion.status_code, 200, sparse_conclusion.text)
        self.assertIn("不能评价多空表现", sparse_conclusion.json()["evidence"][2])
        sparse_report = self.client.get(f"/api/v1/reports/{sparse_only.json()['id']}/html", headers=researcher)
        self.assertEqual(sparse_report.status_code, 200, sparse_report.text)
        self.assertIn("暂无有效时间序列。", sparse_report.text)
        self.assertIn("暂无可计算的分组收益", sparse_report.text)

    def test_comparison_api_and_exports_include_actual_group_dates(self):
        researcher = self.auth("researcher", "research12345")
        run_ids = []
        for factor in ("momentum_20d", "reversal_5d"):
            created = self.client.post("/api/v1/research/tasks", headers=researcher,
                                       json={"factor": factor, "groups": 5, "start_date": "2025-02-03"})
            self.assertEqual(created.status_code, 201, created.text)
            self.assertEqual(created.json()["status"], "success")
            run_ids.append(created.json()["id"])

        payload = {"run_ids": run_ids}
        compared = self.client.post("/api/v1/research/comparisons", headers=researcher, json=payload)
        self.assertEqual(compared.status_code, 200, compared.text)
        result = compared.json()
        self.assertEqual(result["common_group_date_count"], result["common_ic_date_count"])
        self.assertTrue(result["matched_sample"]["available"])
        self.assertGreater(result["matched_sample"]["observation_count"], 0)
        self.assertEqual(result["matched_sample"]["label_mismatch_count"], 0)
        self.assertTrue(all(item["group_date_count"] > 0 for item in result["items"]))

        csv_export = self.client.post("/api/v1/research/comparisons/export.csv", headers=researcher, json=payload)
        self.assertEqual(csv_export.status_code, 200, csv_export.text)
        csv_text = csv_export.content.decode("utf-8-sig")
        self.assertIn("共同多空分组日期数", csv_text)
        self.assertIn("严格样本IC摘要", csv_text)
        html_export = self.client.post("/api/v1/research/comparisons/export.html", headers=researcher, json=payload)
        self.assertEqual(html_export.status_code, 200, html_export.text)
        self.assertIn("共同多空分组日期", html_export.text)
        self.assertIn("严格样本 IC 摘要", html_export.text)

        # The API JSON is the source of the client-side snapshot; check the
        # human-readable exports against its ordered identities and metrics.
        rows = list(csv.DictReader(io.StringIO(csv_text)))[:len(result["items"])]
        self.assertEqual(len(rows), len(result["items"]))
        for item, row in zip(result["items"], rows):
            with self.subTest(run_id=item["run_id"]):
                self.assertEqual(row["run_id"], item["run_id"])
                self.assertEqual(row["dataset_version_id"], item["dataset_version_id"])
                self.assertEqual(row["dataset_checksum_sha256"], item["dataset_checksum_sha256"])
                self.assertAlmostEqual(float(row["ic_mean"]), item["metrics"]["ic_mean"])
                self.assertAlmostEqual(float(row["common_date_ic_mean"]), item["common_date_ic"]["ic_mean"])
                self.assertIn(item["run_id"], html_export.text)
                self.assertIn(item["dataset_version_id"], html_export.text)
                self.assertIn(item["dataset_checksum_sha256"], html_export.text)
                self.assertIn(f"{item['metrics']['ic_mean']:.4f}", html_export.text)
        for warning in result["warnings"]:
            self.assertIn(html.escape(warning), html_export.text)
            self.assertIn(warning, csv_text)

        origin = "http://127.0.0.1:5173"
        for endpoint in (
            "/api/v1/research/comparisons/export.csv",
            "/api/v1/research/comparisons/export.html",
        ):
            with self.subTest(cors_endpoint=endpoint):
                preflight = self.client.options(endpoint, headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "authorization,content-type",
                })
                self.assertEqual(preflight.status_code, 200, preflight.text)
                self.assertEqual(preflight.headers["access-control-allow-origin"], origin)
                self.assertIn("authorization", preflight.headers["access-control-allow-headers"].lower())
                self.assertIn("content-type", preflight.headers["access-control-allow-headers"].lower())
                exported = self.client.post(endpoint, headers={**researcher, "Origin": origin}, json=payload)
                self.assertEqual(exported.status_code, 200, exported.text)
                self.assertEqual(exported.headers["access-control-allow-origin"], origin)
                self.assertTrue(exported.content)
                rejected_origin = self.client.options(endpoint, headers={
                    "Origin": "https://untrusted.example",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "authorization,content-type",
                })
                self.assertEqual(rejected_origin.status_code, 400)
                self.assertNotIn("access-control-allow-origin", rejected_origin.headers)

        for endpoint in (
            "/api/v1/research/comparisons",
            "/api/v1/research/comparisons/export.csv",
            "/api/v1/research/comparisons/export.html",
        ):
            with self.subTest(endpoint=endpoint):
                rejected = self.client.post(endpoint, headers=researcher,
                                            json={"run_ids": [run_ids[0], run_ids[0]]})
                self.assertEqual(rejected.status_code, 400, rejected.text)
                self.assertIn("distinct", rejected.json()["detail"])

    def test_validation_matched_comparison_is_available_through_http_and_exports(self):
        researcher = self.auth("researcher", "research12345")
        run_ids = []
        for factor in ("momentum_20d", "reversal_5d"):
            created = self.client.post("/api/v1/research/tasks", headers=researcher, json={
                "factor": factor, "groups": 5, "start_date": "2025-02-03",
                "validation_start_date": "2025-04-01",
            })
            self.assertEqual(created.status_code, 201, created.text)
            self.assertEqual(created.json()["status"], "success")
            run_ids.append(created.json()["id"])
        payload = {"run_ids": run_ids}
        compared = self.client.post("/api/v1/research/comparisons", headers=researcher, json=payload)
        self.assertEqual(compared.status_code, 200, compared.text)
        matched = compared.json()["matched_validation_sample"]
        self.assertTrue(matched["available"])
        self.assertEqual(matched["validation_start_date"], "2025-04-01")
        self.assertGreater(matched["observation_count"], 0)
        self.assertEqual(len(matched["items"]), 2)
        csv_export = self.client.post("/api/v1/research/comparisons/export.csv", headers=researcher, json=payload)
        self.assertEqual(csv_export.status_code, 200, csv_export.text)
        self.assertIn("验证期严格样本IC摘要", csv_export.content.decode("utf-8-sig"))
        html_export = self.client.post("/api/v1/research/comparisons/export.html", headers=researcher, json=payload)
        self.assertEqual(html_export.status_code, 200, html_export.text)
        self.assertIn("验证期严格样本 IC 摘要", html_export.text)

    def test_upload_publish_research_report_and_role_boundaries(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        viewer = self.auth("viewer", "viewer12345")
        csv_content = SAMPLE_CSV.read_bytes()

        unauthenticated = self.client.get("/api/v1/datasets")
        self.assertEqual(unauthenticated.status_code, 401)
        denied_import = self.client.post(
            "/api/v1/datasets/import", headers=viewer,
            data={"dataset_key": "journey_data", "name": "课程验收样本"},
            files={"file": ("daily_prices.csv", csv_content, "text/csv")},
        )
        self.assertEqual(denied_import.status_code, 403)

        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "journey_data", "name": "课程验收样本"},
            files={"file": ("daily_prices.csv", csv_content, "text/csv")},
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertEqual(dataset["status"], "draft")
        self.assertEqual(dataset["row_count"], 2400)
        dataset_id = dataset["id"]

        preview = self.client.get(f"/api/v1/datasets/{dataset_id}/preview", headers=researcher)
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.json()["preview_count"], 20)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/publish", headers=viewer).status_code, 403)
        unpublished_run = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset_id, "factor": "momentum_20d"},
        )
        self.assertEqual(unpublished_run.status_code, 400)

        published = self.client.post(f"/api/v1/datasets/{dataset_id}/publish", headers=admin)
        self.assertEqual(published.status_code, 200, published.text)
        self.assertEqual(published.json()["status"], "published")
        self.assertEqual(self.client.post(
            "/api/v1/research/tasks", headers=viewer,
            json={"dataset_version_id": dataset_id},
        ).status_code, 403)

        created = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset_id, "factor": "momentum_20d", "groups": 5},
        )
        self.assertEqual(created.status_code, 201, created.text)
        task = created.json()
        self.assertEqual(task["status"], "success")
        self.assertEqual(task["dataset_version_id"], dataset_id)
        self.assertGreater(task["result"]["coverage"], 0)
        task_id = task["id"]

        logs = self.client.get(f"/api/v1/research/tasks/{task_id}/logs", headers=researcher)
        self.assertEqual(logs.status_code, 200, logs.text)
        self.assertTrue(any(item["event"] == "completed" for item in logs.json()))
        bundle = self.client.get(f"/api/v1/research/tasks/{task_id}/reproducibility.json", headers=researcher)
        self.assertEqual(bundle.status_code, 200, bundle.text)
        self.assertEqual(bundle.json()["dataset"]["checksum_sha256"], dataset["checksum"])
        self.assertEqual(bundle.json()["result"]["coverage"], task["result"]["coverage"])

        report = self.client.get(f"/api/v1/reports/{task_id}/download", headers=researcher)
        self.assertEqual(report.status_code, 200, report.text)
        self.assertIn("因子研究报告", report.text)
        self.assertIn("attachment", report.headers["content-disposition"])
        detail = report.text.split('<details class="series-detail">', 1)[1].split("</details>", 1)[0]
        result = bundle.json()["result"]
        dates = sorted(
            {item["date"] for item in result["ic_series"]} |
            {item["date"] for item in result["long_short_series"]} |
            {item["date"] for item in result["daily_coverage"]} |
            {point["date"] for group in result["group_nav"] for point in group["points"]}
        )
        self.assertIn(f"{len(dates)} 个已知日期", detail)
        self.assertEqual(detail.count("<tr>"), len(dates) + 1)
        self.assertEqual(detail.count(" 净值</th>"), len(result["group_nav"]))
        self.assertIn("<th>IC 状态</th><th>分组状态</th>", detail)
        ic_by_date = {item["date"]: item for item in result["ic_series"]}
        nav_by_date = {item["date"]: item for item in result["long_short_series"]}
        coverage_by_date = {item["date"]: item for item in result["daily_coverage"]}
        group_by_date = [{point["date"]: point["nav"] for point in group["points"]}
                         for group in result["group_nav"]]
        status_labels = {"valid": "可计算", "insufficient_sample": "样本不足", "no_observation": "无有效观测",
                         "constant_factor": "因子同值", "constant_factor_or_return": "常量截面"}
        for date in dates:
            ic = ic_by_date.get(date, {})
            nav = nav_by_date.get(date, {})
            cells = [ic.get("ic"), ic.get("rank_ic"), nav.get("nav"), nav.get("net_nav")]
            cells.extend(group.get(date) for group in group_by_date)
            expected = f'<tr><td>{date}</td>' + "".join(
                "<td>" + ("—" if value is None else format(value, ".4f")) + "</td>" for value in cells
            )
            diagnostic = coverage_by_date.get(date, {})
            expected += "".join(
                "<td>" + ("—" if status is None else status_labels.get(status, status)) + "</td>"
                for status in (diagnostic.get("ic_status"), diagnostic.get("group_status"))
            ) + "</tr>"
            self.assertIn(expected, detail)
        preview = self.client.get(f"/api/v1/reports/{task_id}/html", headers=viewer)
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.content, report.content)
        delivery = self.client.get(f"/api/v1/reports/{task_id}/delivery", headers=researcher)
        self.assertEqual(delivery.status_code, 200, delivery.text)
        self.assertIn('<details class="series-detail">' + detail + "</details>", delivery.text)
        self.assertEqual(delivery.headers["x-archived-report-sha256"], hashlib.sha256(report.content).hexdigest())

        second = self.client.post(
            "/api/v1/users", headers=admin,
            json={"username": "second_researcher", "display_name": "第二研究员", "password": "second-pass123", "role": "researcher"},
        )
        self.assertEqual(second.status_code, 201, second.text)
        other_researcher = self.auth("second_researcher", "second-pass123")
        self.assertFalse(any(item["id"] == task_id for item in self.client.get("/api/v1/research/tasks", headers=other_researcher).json()))
        self.assertFalse(any(item["run_id"] == task_id for item in self.client.get("/api/v1/reports", headers=other_researcher).json()))
        for path in (
            f"/api/v1/research/tasks/{task_id}",
            f"/api/v1/research/tasks/{task_id}/logs",
            f"/api/v1/research/tasks/{task_id}/reproducibility.json",
            f"/api/v1/reports/{task_id}/html",
            f"/api/v1/reports/{task_id}/download",
            f"/api/v1/reports/{task_id}/delivery",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=other_researcher).status_code, 403)

    def test_failed_historical_task_retries_in_historical_mode(self):
        researcher = self.auth("researcher", "research12345")
        viewer = self.auth("viewer", "viewer12345")
        with Session(self.engine) as session:
            owner = session.query(User).filter_by(username="researcher").one()
            dataset = DatasetVersion(
                dataset_key="hs300_2024", name="retry fixture", version="retry-fixture",
                checksum="0" * 64, storage_uri="/unused/manifest.json", source_filename="manifest.json",
                quality_report={"dataset_kind": "hs300_bundle_v1"}, status="published",
            )
            session.add(dataset)
            session.commit()
            source = create_historical_run(session, {"dataset_version_id": dataset.id, "groups": 3},
                                           created_by_id=owner.id)
            source.status = RunStatus.FAILED
            source.error_summary = "isolated fixture failure"
            session.commit()
            source_id, dataset_id = source.id, dataset.id

        url = f"/api/v1/research/tasks/{source_id}/retry"
        self.assertEqual(self.client.post(url, headers=viewer).status_code, 403)
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            response = self.client.post(url, headers=researcher)
        self.assertEqual(response.status_code, 201, response.text)
        retried = response.json()
        self.assertNotEqual(retried["id"], source_id)
        self.assertEqual(retried["status"], "pending")
        self.assertEqual(retried["dataset_version_id"], dataset_id)
        self.assertEqual(retried["parameters"]["mode"], "historical_hs300_2024")
        self.assertEqual(retried["parameters"]["groups"], 3)
        self.assertEqual(len(retried["parameters"]["components"]), 4)
        enqueue.assert_called_once_with(args=[retried["id"]], task_id=retried["id"])
        self.assertEqual(self.client.get(f"/api/v1/research/tasks/{source_id}", headers=researcher).json()["status"],
                         "failed")
        with Session(self.engine) as session:
            session.get(DatasetVersion, dataset_id).status = "draft"
            session.commit()
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            unavailable = self.client.post(url, headers=researcher)
        self.assertEqual(unavailable.status_code, 400, unavailable.text)
        enqueue.assert_not_called()

    def test_pending_task_cancel_permissions_and_retry_http_journey(self):
        researcher = self.auth("researcher", "research12345")
        viewer = self.auth("viewer", "viewer12345")
        admin = self.auth("admin", "admin12345")
        created_user = self.client.post(
            "/api/v1/users", headers=admin,
            json={"username": "other_researcher", "display_name": "其他研究员",
                  "password": "other-pass123", "role": "researcher"},
        )
        self.assertEqual(created_user.status_code, 201, created_user.text)
        other = self.auth("other_researcher", "other-pass123")

        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            created = self.client.post("/api/v1/research/tasks", headers=researcher,
                                       json={"factor": "momentum_20d", "groups": 5})
        self.assertEqual(created.status_code, 201, created.text)
        source = created.json()
        self.assertEqual(source["status"], "pending")
        enqueue.assert_called_once_with(args=[source["id"]], task_id=source["id"])
        path = f"/api/v1/research/tasks/{source['id']}"

        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.celery_app.control.revoke") as revoke:
            self.assertEqual(self.client.post(f"{path}/cancel", headers=viewer).status_code, 403)
            self.assertEqual(self.client.post(f"{path}/cancel", headers=other).status_code, 403)
            cancelled = self.client.post(f"{path}/cancel", headers=researcher)
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        self.assertEqual(cancelled.json()["status"], "cancelled")
        revoke.assert_called_once_with(source["id"], terminate=False)
        self.assertEqual([item["event"] for item in self.client.get(f"{path}/logs", headers=researcher).json()],
                         ["queued", "cancelled"])
        self.assertEqual(self.client.post(f"{path}/cancel", headers=researcher).status_code, 409)
        self.assertEqual(self.client.post(f"{path}/retry", headers=viewer).status_code, 403)
        self.assertEqual(self.client.post(f"{path}/retry", headers=other).status_code, 403)

        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            retried = self.client.post(f"{path}/retry", headers=researcher)
        self.assertEqual(retried.status_code, 201, retried.text)
        self.assertNotEqual(retried.json()["id"], source["id"])
        self.assertEqual(retried.json()["status"], "pending")
        self.assertEqual(retried.json()["parameters"], source["parameters"])
        enqueue.assert_called_once_with(args=[retried.json()["id"]], task_id=retried.json()["id"])
        self.assertEqual(self.client.get(path, headers=researcher).json()["status"], "cancelled")
        self.assertEqual(self.client.post(f"/api/v1/research/tasks/{retried.json()['id']}/retry",
                                          headers=researcher).status_code, 409)

    def test_broker_connection_failure_records_failed_run_and_allows_retry(self):
        researcher = self.auth("researcher", "research12345")
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async", side_effect=OperationalError("redis unavailable")):
            response = self.client.post("/api/v1/research/tasks", headers=researcher,
                                        json={"factor": "momentum_20d", "groups": 5})
        self.assertEqual(response.status_code, 503, response.text)
        self.assertNotIn("redis unavailable", response.text)
        tasks = self.client.get("/api/v1/research/tasks", headers=researcher).json()
        self.assertEqual(len(tasks), 1)
        failed = tasks[0]
        self.assertEqual(failed["status"], "failed")
        self.assertIn("消息队列连接失败", failed["error_summary"])
        logs = self.client.get(f"/api/v1/research/tasks/{failed['id']}/logs", headers=researcher).json()
        self.assertTrue(any(item["event"] == "failed" for item in logs))
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            retried = self.client.post(f"/api/v1/research/tasks/{failed['id']}/retry", headers=researcher)
        self.assertEqual(retried.status_code, 201, retried.text)
        self.assertEqual(retried.json()["status"], "pending")
        enqueue.assert_called_once()

    def test_broker_error_does_not_overwrite_already_claimed_run(self):
        researcher = self.auth("researcher", "research12345")

        def claimed_then_error(*, args, task_id):
            with Session(self.engine) as session:
                _, claimed = claim_pending_run(session, task_id)
                self.assertTrue(claimed)
            raise OperationalError("redis ack unavailable")

        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async", side_effect=claimed_then_error):
            response = self.client.post("/api/v1/research/tasks", headers=researcher,
                                        json={"factor": "momentum_20d", "groups": 5})
        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("请先检查任务状态", response.json()["detail"])
        task = self.client.get("/api/v1/research/tasks", headers=researcher).json()[0]
        self.assertEqual(task["status"], "running")
        events = [item["event"] for item in self.client.get(
            f"/api/v1/research/tasks/{task['id']}/logs", headers=researcher,
        ).json()]
        self.assertEqual(events, ["queued", "started"])

    def test_historical_audit_csv_requires_owner_and_completed_historical_run(self):
        researcher = self.auth("researcher", "research12345")
        viewer = self.auth("viewer", "viewer12345")
        with Session(self.engine) as session:
            owner = session.query(User).filter_by(username="researcher").one()
            dataset = DatasetVersion(
                dataset_key="hs300_2024", name="audit fixture", version="fixture",
                checksum="0" * 64, storage_uri="/unused/manifest.json", source_filename="manifest.json",
                quality_report={"dataset_kind": "hs300_bundle_v1"}, status="published",
            )
            session.add(dataset)
            session.commit()
            run = create_historical_run(session, {"dataset_version_id": dataset.id}, created_by_id=owner.id)
            task_id = run.id
        daily_url = f"/api/v1/research/tasks/{task_id}/historical-audit/daily.csv"
        self.assertEqual(self.client.get(daily_url).status_code, 401)
        self.assertEqual(self.client.get(daily_url, headers=researcher).status_code, 409)

        with Session(self.engine) as session:
            run = session.get(Run, task_id)
            run.status = RunStatus.SUCCESS
            run.artifacts.append(Artifact(artifact_type="metrics", name="result.json", content={
                "historical_audit": {
                    "momentum_20d": {
                        "daily": [{"date": "2024-01-02", "candidate_count": 300, "valid_return": 299},
                                  {"date": "2024-01-03", "candidate_count": 300}],
                        "unlabeled_signals": [{"date": "2024-01-02", "symbol": "sh.600000", "factor": 0.1,
                                               "next_market_date": "2024-01-03", "reason": "label_suspended"}],
                    },
                },
            }))
            session.commit()

        daily = self.client.get(daily_url, headers=researcher)
        self.assertEqual(daily.status_code, 200, daily.text)
        self.assertTrue(daily.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn("momentum_20d,2024-01-02,300,299", daily.content.decode("utf-8-sig"))
        self.assertIn("momentum_20d,2024-01-03,300,0", daily.content.decode("utf-8-sig"))
        self.assertIn("attachment", daily.headers["content-disposition"])
        unlabeled = self.client.get(
            f"/api/v1/research/tasks/{task_id}/historical-audit/unlabeled.csv", headers=viewer,
        )
        self.assertEqual(unlabeled.status_code, 200, unlabeled.text)
        self.assertIn("sh.600000,0.1,2024-01-03,label_suspended", unlabeled.content.decode("utf-8-sig"))
        self.assertEqual(self.client.get(
            f"/api/v1/research/tasks/{task_id}/historical-audit/unknown.csv", headers=researcher,
        ).status_code, 409)

        self.client.post("/api/v1/users", headers=self.auth("admin", "admin12345"), json={
            "username": "other_audit", "display_name": "其他研究员", "password": "second-pass123", "role": "researcher",
        })
        other = self.auth("other_audit", "second-pass123")
        self.assertEqual(self.client.get(daily_url, headers=other).status_code, 403)


if __name__ == "__main__":
    unittest.main()
