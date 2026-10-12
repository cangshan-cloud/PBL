"""独立验证三种角色的 API 权限边界，不读写开发数据库。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="factorlab-permissions-") as temp_dir:
        root = Path(temp_dir)
        os.environ["DATABASE_URL"] = f"sqlite:///{root / 'permissions.db'}"
        os.environ["DATA_ROOT"] = str(root / "data")
        os.environ["TASK_EXECUTION_MODE"] = "inline"
        os.environ["JWT_SECRET"] = "permission-verification-only-secret"

        from fastapi.testclient import TestClient

        from app.db import SessionLocal
        from app.main import app
        from app.services.runs import create_research_run

        def expect(response, status: int):
            assert response.status_code == status, response.text
            return response

        def login(client: TestClient, username: str, password: str) -> dict[str, str]:
            response = expect(
                client.post("/api/v1/auth/login", json={"username": username, "password": password}),
                200,
            )
            return {"Authorization": f"Bearer {response.json()['access_token']}"}

        with TestClient(app) as client:
            expect(client.get("/api/v1/datasets"), 401)
            admin = login(client, "admin", "admin12345")
            researcher = login(client, "researcher", "research12345")
            viewer = login(client, "viewer", "viewer12345")

            expect(client.get("/api/v1/users", headers=admin), 200)
            expect(client.get("/api/v1/users", headers=researcher), 403)
            expect(
                client.post(
                    "/api/v1/users",
                    headers=admin,
                    json={
                        "username": "researcher2",
                        "display_name": "研究员二号",
                        "password": "researcher2-pass",
                        "role": "researcher",
                    },
                ),
                201,
            )
            researcher2 = login(client, "researcher2", "researcher2-pass")

            datasets = expect(client.get("/api/v1/datasets", headers=researcher), 200).json()
            demo_id = next(item["id"] for item in datasets if item["dataset_key"] == "demo_daily")
            cn_source = "日期,股票代码,开盘,最高,最低,收盘,成交量\n2025/01/02,600000,8,8.5,7.8,8.2,900\n".encode("gb18030")
            expect(
                client.post(
                    "/api/v1/datasets/adapt/preview",
                    headers=researcher,
                    files={"file": ("source.csv", cn_source, "text/csv")},
                ),
                403,
            )
            adapted_preview = expect(
                client.post(
                    "/api/v1/datasets/adapt/preview",
                    headers=admin,
                    files={"file": ("source.csv", cn_source, "text/csv")},
                ),
                200,
            ).json()
            assert adapted_preview["preview"][0]["symbol"] == "600000.SH"
            adapted_dataset = expect(
                client.post(
                    "/api/v1/datasets/import",
                    headers=admin,
                    data={"dataset_key": "adapted_demo", "name": "适配演示", "normalize_cn_csv": "true"},
                    files={"file": ("source.csv", cn_source, "text/csv")},
                ),
                201,
            ).json()
            assert adapted_dataset["quality_report"]["adapter_report"]["adapter"] == "cn_stock_csv_auto"
            preview = expect(client.get(f"/api/v1/datasets/{demo_id}/preview?limit=5", headers=researcher), 200).json()
            assert preview["preview_count"] == 5 and preview["truncated"] is True
            expect(client.get(f"/api/v1/datasets/{demo_id}/preview"), 401)
            expect(client.get("/api/v1/datasets/not-found/preview", headers=researcher), 404)
            factors = expect(client.get("/api/v1/factors", headers=researcher), 200).json()
            assert len(factors) == 6
            assert all(item["status"] == "available" for item in factors)
            task_payload = {
                "factor": "momentum_20d",
                "dataset_version_id": demo_id,
                "lookback": 20,
                "groups": 5,
            }
            expect(client.post("/api/v1/research/tasks", headers=viewer, json=task_payload), 403)
            turnover = expect(
                client.post(
                    "/api/v1/research/tasks",
                    headers=researcher,
                    json={**task_payload, "factor": "turnover_20d"},
                ),
                201,
            ).json()
            assert turnover["status"] == "success"
            assert turnover["result"]["coverage"] == 2000
            first = expect(
                client.post(
                    "/api/v1/research/tasks",
                    headers=researcher,
                    json={
                        **task_payload,
                        "factor": "reversal_5d",
                        "lookback": 5,
                        "groups": 2,
                        "symbols": ["DEMO01", "DEMO02"],
                        "start_date": "2025-01-10",
                        "end_date": "2025-01-14",
                    },
                ),
                201,
            ).json()
            assert first["status"] == "success"
            assert first["result"]["coverage"] == 6
            assert first["result"]["sample"]["resolved_symbol_count"] == 2
            assert first["result"]["preprocessing"]["method"] == "MAD"
            assert "long_short_series" in first["result"]
            assert "top_group_turnover" in first["result"]
            conclusion = expect(
                client.get(f"/api/v1/research/tasks/{first['id']}/conclusion", headers=researcher),
                200,
            ).json()
            assert conclusion["method"]["type"] == "deterministic_rule_template"
            assert conclusion["limitations"]
            composite = expect(
                client.post(
                    "/api/v1/research/composite-tasks",
                    headers=researcher,
                    json={
                        "dataset_version_id": demo_id,
                        "factors": ["momentum_20d", "reversal_5d"],
                        "lookbacks": {"momentum_20d": 20, "reversal_5d": 5},
                        "groups": 5,
                    },
                ),
                201,
            ).json()
            assert composite["status"] == "success"
            assert composite["result"]["composite"]["common_coverage"] == 1980
            comparison = expect(
                client.post(
                    "/api/v1/research/comparisons",
                    headers=researcher,
                    json={"run_ids": [turnover["id"], composite["id"]]},
                ),
                200,
            ).json()
            assert len(comparison["items"]) == 2
            assert comparison["common_ic_date_count"] > 0
            csv_export = expect(
                client.post(
                    "/api/v1/research/comparisons/export.csv",
                    headers=researcher,
                    json={"run_ids": [turnover["id"], composite["id"]]},
                ),
                200,
            )
            assert csv_export.content.startswith(b"\xef\xbb\xbf")
            assert "attachment" in csv_export.headers["content-disposition"]
            html_export = expect(
                client.post(
                    "/api/v1/research/comparisons/export.html",
                    headers=researcher,
                    json={"run_ids": [turnover["id"], composite["id"]]},
                ),
                200,
            )
            assert "实验对比报告" in html_export.text
            expect(
                client.post(
                    "/api/v1/research/composite-tasks",
                    headers=viewer,
                    json={"dataset_version_id": demo_id, "factors": ["momentum_20d", "reversal_5d"]},
                ),
                403,
            )
            second = expect(
                client.post("/api/v1/research/tasks", headers=researcher2, json=task_payload), 201
            ).json()
            expect(
                client.post(
                    "/api/v1/research/comparisons",
                    headers=researcher,
                    json={"run_ids": [first["id"], second["id"]]},
                ),
                403,
            )
            expect(
                client.post(
                    "/api/v1/research/comparisons",
                    headers=viewer,
                    json={"run_ids": [first["id"], second["id"]]},
                ),
                200,
            )

            researcher_dashboard = expect(client.get("/api/v1/dashboard", headers=researcher), 200).json()
            viewer_dashboard = expect(client.get("/api/v1/dashboard", headers=viewer), 200).json()
            assert researcher_dashboard["scope"] == "personal" and researcher_dashboard["tasks"]["total"] == 3
            assert viewer_dashboard["scope"] == "global" and viewer_dashboard["tasks"]["total"] == 4

            own_tasks = expect(client.get("/api/v1/research/tasks", headers=researcher), 200).json()
            assert {item["id"] for item in own_tasks} == {turnover["id"], first["id"], composite["id"]}
            expect(client.get(f"/api/v1/research/tasks/{second['id']}", headers=researcher), 403)
            expect(client.get(f"/api/v1/research/tasks/{second['id']}/conclusion", headers=researcher), 403)
            expect(client.get(f"/api/v1/research/tasks/{second['id']}/conclusion", headers=viewer), 200)
            viewer_tasks = expect(client.get("/api/v1/research/tasks", headers=viewer), 200).json()
            assert {item["id"] for item in viewer_tasks} == {turnover["id"], first["id"], composite["id"], second["id"]}

            reports = expect(client.get("/api/v1/reports", headers=researcher), 200).json()
            assert {item["run_id"] for item in reports} == {turnover["id"], first["id"], composite["id"]}
            expect(client.get(f"/api/v1/reports/{second['id']}/html", headers=researcher), 403)

            expect(client.get(f"/api/v1/research/tasks/{first['id']}/logs", headers=researcher), 200)
            expect(client.get(f"/api/v1/research/tasks/{second['id']}/logs", headers=researcher), 403)
            expect(client.get(f"/api/v1/research/tasks/{second['id']}/logs", headers=viewer), 200)
            expect(client.post(f"/api/v1/research/tasks/{first['id']}/cancel", headers=researcher), 409)
            expect(client.post(f"/api/v1/research/tasks/{first['id']}/cancel", headers=viewer), 403)

            researcher_id = expect(client.get("/api/v1/auth/me", headers=researcher), 200).json()["id"]
            with SessionLocal() as session:
                pending = create_research_run(session, task_payload, created_by_id=researcher_id)
                pending_id = pending.id
            cancelled = expect(
                client.post(f"/api/v1/research/tasks/{pending_id}/cancel", headers=researcher), 200
            ).json()
            assert cancelled["status"] == "cancelled"
            retried = expect(
                client.post(f"/api/v1/research/tasks/{pending_id}/retry", headers=researcher), 201
            ).json()
            assert retried["id"] != pending_id and retried["status"] == "success"

            managed = expect(
                client.post(
                    "/api/v1/users",
                    headers=admin,
                    json={
                        "username": "managed_viewer",
                        "display_name": "受管只读用户",
                        "password": "managed-pass1",
                        "role": "viewer",
                    },
                ),
                201,
            ).json()
            managed_headers = login(client, "managed_viewer", "managed-pass1")
            expect(client.patch(f"/api/v1/users/{managed['id']}", headers=researcher, json={"is_active": False}), 403)
            expect(client.patch(f"/api/v1/users/{managed['id']}", headers=admin, json={"is_active": False}), 200)
            expect(client.get("/api/v1/auth/me", headers=managed_headers), 401)
            expect(client.post("/api/v1/auth/login", json={"username": "managed_viewer", "password": "managed-pass1"}), 401)
            expect(client.patch(f"/api/v1/users/{managed['id']}", headers=admin, json={"is_active": True, "role": "researcher"}), 200)
            restored_headers = login(client, "managed_viewer", "managed-pass1")
            assert expect(client.get("/api/v1/auth/me", headers=restored_headers), 200).json()["role"] == "researcher"
            admin_id = expect(client.get("/api/v1/auth/me", headers=admin), 200).json()["id"]
            expect(client.patch(f"/api/v1/users/{admin_id}", headers=admin, json={"is_active": False}), 409)

        print("权限矩阵验证通过：未登录、管理员、研究员、只读用户边界均符合预期。")


if __name__ == "__main__":
    main()
