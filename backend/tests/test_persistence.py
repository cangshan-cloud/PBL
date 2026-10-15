import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Run, RunStatus
from app.services.datasets import import_csv, publish_dataset_version
from app.services.runs import claim_pending_run, create_research_run, execute_research_run, fail_pending_enqueue, get_run, list_run_logs, request_cancellation, transition
from app.services.sample_data import sample_file


def _validate_test_database_url(database_url: str) -> str:
    target = make_url(database_url)
    if (target.drivername != "postgresql+psycopg" or target.database != "factorlab_test_concurrency"
            or target.host not in {"127.0.0.1", "localhost"} or target.username != "factorlab_test"):
        raise ValueError("FACTORLAB_TEST_DATABASE_URL must target the dedicated loopback test database")
    return database_url


class TestDatabaseTargetGuard(unittest.TestCase):
    def test_only_dedicated_loopback_postgres_target_is_allowed(self):
        allowed = "postgresql+psycopg://factorlab_test:secret@127.0.0.1:5432/factorlab_test_concurrency"
        self.assertEqual(_validate_test_database_url(allowed), allowed)
        for forbidden in (
            "postgresql+psycopg://factorlab_test:secret@127.0.0.1:5432/factorlab",
            "postgresql+psycopg://factorlab_test:secret@db:5432/factorlab_test_concurrency",
            "postgresql+psycopg://factorlab:secret@127.0.0.1:5432/factorlab_test_concurrency",
            "sqlite:///factorlab_test_concurrency.db",
        ):
            with self.subTest(forbidden=forbidden), self.assertRaisesRegex(ValueError, "dedicated loopback"):
                _validate_test_database_url(forbidden)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_url = os.getenv("FACTORLAB_TEST_DATABASE_URL")
        if database_url:
            try:
                self.engine = create_engine(_validate_test_database_url(database_url))
            except (ValueError, TypeError):
                self.temp_dir.cleanup()
                raise
        else:
            database_path = Path(self.temp_dir.name) / "test.db"
            self.engine = create_engine(f"sqlite:///{database_path}")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_run_result_survives_new_session(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(
                session,
                {"factor": "momentum_20d", "lookback": 20, "groups": 5},
            )
            run_id = run.id
            completed = execute_research_run(session, run_id)
            self.assertEqual(completed.status, RunStatus.SUCCESS)
            self.assertEqual(completed.progress, 100)
            self.assertEqual(len(completed.artifacts), 2)
            self.assertTrue(completed.experiment.code_version.startswith("src-sha256:"))

        with Session(self.engine) as another_session:
            restored = get_run(another_session, run_id)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.status, RunStatus.SUCCESS)
            metrics = next(item for item in restored.artifacts if item.artifact_type == "metrics")
            report = next(item for item in restored.artifacts if item.artifact_type == "report_html")
            self.assertEqual(metrics.content["coverage"], 1980)
            self.assertTrue(Path(report.storage_uri).is_file())

    def test_worker_rejects_task_created_by_different_source_version(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            run.experiment.code_version = "src-sha256:" + "0" * 64
            session.commit()
            with self.assertRaisesRegex(ValueError, "代码指纹"):
                execute_research_run(session, run.id)
            failed = get_run(session, run.id)
            self.assertEqual(failed.status, RunStatus.FAILED)
            self.assertIn("代码指纹", failed.error_summary)
            self.assertEqual(list_run_logs(session, run.id)[-1].event, "failed")

    def test_terminal_run_cannot_restart(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(
                session,
                {"factor": "momentum_20d", "lookback": 20, "groups": 5},
            )
            completed = execute_research_run(session, run.id)
            with self.assertRaisesRegex(ValueError, "invalid run transition"):
                transition(session, completed, RunStatus.RUNNING)

    def test_late_or_duplicate_delivery_does_not_reexecute_nonpending_run(self):
        with Session(self.engine, expire_on_commit=False) as session:
            succeeded = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            completed = execute_research_run(session, succeeded.id)
            before_events = [item.event for item in list_run_logs(session, succeeded.id)]
            before_artifacts = [item.id for item in completed.artifacts]
            replayed = execute_research_run(session, succeeded.id)
            self.assertEqual(replayed.status, RunStatus.SUCCESS)
            self.assertEqual([item.event for item in list_run_logs(session, succeeded.id)], before_events)
            self.assertEqual([item.id for item in replayed.artifacts], before_artifacts)

            cancelled = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            request_cancellation(session, cancelled, "测试用户")
            self.assertEqual(execute_research_run(session, cancelled.id).status, RunStatus.CANCELLED)
            self.assertEqual([item.event for item in list_run_logs(session, cancelled.id)], ["queued", "cancelled"])

            failed = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            transition(session, failed, RunStatus.FAILED, error="消息队列连接失败，任务未能入队")
            self.assertEqual(execute_research_run(session, failed.id).status, RunStatus.FAILED)
            self.assertEqual([item.event for item in list_run_logs(session, failed.id)], ["queued", "failed"])

            running = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            transition(session, running, RunStatus.RUNNING)
            self.assertEqual(execute_research_run(session, running.id).status, RunStatus.RUNNING)
            self.assertEqual([item.event for item in list_run_logs(session, running.id)], ["queued", "started"])

    def test_two_workers_can_claim_a_pending_run_only_once(self):
        with Session(self.engine) as session:
            run_id = create_research_run(session, {"factor": "momentum_20d", "groups": 5}).id
        barrier = Barrier(2)

        def attempt_claim() -> bool:
            with Session(self.engine) as session:
                barrier.wait(timeout=5)
                _, claimed = claim_pending_run(session, run_id)
                return claimed

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: attempt_claim(), range(2)))
        self.assertEqual(sorted(outcomes), [False, True])
        with Session(self.engine) as session:
            run = get_run(session, run_id)
            self.assertEqual(run.status, RunStatus.RUNNING)
            self.assertEqual(run.progress, 5)
            self.assertIsNotNone(run.started_at)
            self.assertEqual([item.event for item in list_run_logs(session, run_id)], ["queued", "started"])

    def test_cancellation_and_worker_claim_have_one_consistent_outcome(self):
        for _ in range(5):
            with Session(self.engine) as session:
                run_id = create_research_run(session, {"factor": "momentum_20d", "groups": 5}).id
            barrier = Barrier(2)

            def claim() -> bool:
                with Session(self.engine) as session:
                    barrier.wait(timeout=5)
                    return claim_pending_run(session, run_id)[1]

            def cancel() -> RunStatus:
                with Session(self.engine) as session:
                    barrier.wait(timeout=5)
                    return request_cancellation(session, Run(id=run_id), "测试用户").status

            with ThreadPoolExecutor(max_workers=2) as pool:
                claim_future = pool.submit(claim)
                cancel_future = pool.submit(cancel)
                claimed, cancelled_status = claim_future.result(), cancel_future.result()
            with Session(self.engine) as session:
                run = get_run(session, run_id)
                events = [item.event for item in list_run_logs(session, run_id)]
                if claimed:
                    self.assertEqual(cancelled_status, RunStatus.RUNNING)
                    self.assertEqual(run.status, RunStatus.RUNNING)
                    self.assertIsNotNone(run.cancellation_requested_at)
                    self.assertEqual(events, ["queued", "started", "cancellation_requested"])
                else:
                    self.assertEqual(cancelled_status, RunStatus.CANCELLED)
                    self.assertEqual(run.status, RunStatus.CANCELLED)
                    self.assertEqual(events, ["queued", "cancelled"])

    def test_broker_failure_and_worker_claim_cannot_both_win(self):
        for _ in range(5):
            with Session(self.engine) as session:
                run_id = create_research_run(session, {"factor": "momentum_20d", "groups": 5}).id
            barrier = Barrier(2)

            def claim() -> bool:
                with Session(self.engine) as session:
                    barrier.wait(timeout=5)
                    return claim_pending_run(session, run_id)[1]

            def fail_enqueue() -> bool:
                with Session(self.engine) as session:
                    barrier.wait(timeout=5)
                    return fail_pending_enqueue(session, run_id)

            with ThreadPoolExecutor(max_workers=2) as pool:
                claim_future = pool.submit(claim)
                failure_future = pool.submit(fail_enqueue)
                claimed, marked_failed = claim_future.result(), failure_future.result()
            self.assertNotEqual(claimed, marked_failed)
            with Session(self.engine) as session:
                run = get_run(session, run_id)
                events = [item.event for item in list_run_logs(session, run_id)]
                self.assertEqual(run.status, RunStatus.RUNNING if claimed else RunStatus.FAILED)
                self.assertEqual(events, ["queued", "started" if claimed else "failed"])

    def test_pending_run_can_be_cancelled_with_audit_log(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            cancelled = request_cancellation(session, run, "测试用户")
            self.assertEqual(cancelled.status, RunStatus.CANCELLED)
            self.assertIsNotNone(cancelled.finished_at)
            events = [item.event for item in list_run_logs(session, run.id)]
            self.assertEqual(events, ["queued", "cancelled"])
            with self.assertRaisesRegex(ValueError, "terminal run"):
                request_cancellation(session, cancelled, "测试用户")

    def test_running_run_records_cooperative_cancellation_request(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            transition(session, run, RunStatus.RUNNING)
            requested = request_cancellation(session, run, "测试用户")
            self.assertEqual(requested.status, RunStatus.RUNNING)
            self.assertIsNotNone(requested.cancellation_requested_at)
            self.assertEqual(list_run_logs(session, run.id)[-1].event, "cancellation_requested")

    def test_successful_run_records_execution_stages(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            execute_research_run(session, run.id)
            events = {item.event for item in list_run_logs(session, run.id)}
            self.assertTrue({"queued", "started", "dataset_loaded", "factor_calculated", "metrics_calculated", "completed"} <= events)

    def test_run_reads_selected_published_dataset(self):
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = import_csv(
                session,
                content=sample_file().read_bytes(),
                source_filename="selected.csv",
                dataset_key="selected_demo",
                name="指定数据版本",
                data_root=Path(self.temp_dir.name),
            )
            with self.assertRaisesRegex(ValueError, "must be published"):
                create_research_run(
                    session,
                    {"factor": "momentum_20d", "dataset_version_id": dataset.id, "lookback": 20, "groups": 5},
                )
            publish_dataset_version(session, dataset)
            run = create_research_run(
                session,
                {"factor": "momentum_20d", "dataset_version_id": dataset.id, "lookback": 20, "groups": 5},
            )
            completed = execute_research_run(session, run.id)
            self.assertEqual(completed.status, RunStatus.SUCCESS)
            self.assertEqual(completed.experiment.dataset_version_id, dataset.id)
            metrics = next(item for item in completed.artifacts if item.artifact_type == "metrics")
            self.assertEqual(metrics.content["coverage"], 1980)

    def test_run_filters_symbols_and_dates_after_using_prior_history(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(
                session,
                {
                    "factor": "reversal_5d",
                    "lookback": 5,
                    "groups": 2,
                    "symbols": ["DEMO01", "DEMO02", "DEMO01"],
                    "start_date": "2025-01-10",
                    "end_date": "2025-01-14",
                },
            )
            completed = execute_research_run(session, run.id)
            metrics = next(item.content for item in completed.artifacts if item.artifact_type == "metrics")
            self.assertEqual(metrics["coverage"], 6)
            self.assertEqual(metrics["sample"]["resolved_symbol_count"], 2)
            self.assertEqual(completed.experiment.parameters["symbols"], ["DEMO01", "DEMO02"])
            factor_dates = [item["date"] for item in metrics["ic_series"]]
            self.assertEqual(factor_dates, ["2025-01-10", "2025-01-13", "2025-01-14"])

    def test_invalid_sample_range_or_symbols_is_rejected(self):
        with Session(self.engine, expire_on_commit=False) as session:
            with self.assertRaisesRegex(ValueError, "start_date"):
                create_research_run(
                    session,
                    {"factor": "momentum_20d", "groups": 5, "start_date": "2025-02-01", "end_date": "2025-01-01"},
                )
            run = create_research_run(
                session,
                {"factor": "momentum_20d", "groups": 5, "symbols": ["UNKNOWN"]},
            )
            with self.assertRaisesRegex(ValueError, "do not exist"):
                execute_research_run(session, run.id)
            sparse = create_research_run(
                session,
                {"factor": "reversal_5d", "lookback": 5, "groups": 5, "symbols": ["DEMO01", "DEMO02"]},
            )
            with self.assertRaisesRegex(ValueError, "fewer symbols"):
                execute_research_run(session, sparse.id)

    def test_modified_dataset_fails_checksum_verification(self):
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = import_csv(
                session,
                content=sample_file().read_bytes(),
                source_filename="integrity.csv",
                dataset_key="integrity_demo",
                name="完整性测试数据",
                data_root=Path(self.temp_dir.name),
            )
            publish_dataset_version(session, dataset)
            run = create_research_run(
                session,
                {"factor": "momentum_20d", "dataset_version_id": dataset.id, "lookback": 20, "groups": 5},
            )
            Path(dataset.storage_uri).write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                execute_research_run(session, run.id)
            failed = get_run(session, run.id)
            self.assertEqual(failed.status, RunStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
