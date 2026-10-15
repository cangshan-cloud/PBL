# CHG-20261015-007：入队失败标记与 Worker 认领互斥

- 日期：2026-10-15
- 类型：task concurrency fix + regressions
- 状态：本机测试通过
- 关联提交：与本记录同次提交

## 背景与决策过程

入队连接失败处理此前先读 Run 状态，再通过普通 ORM 转换把 `pending` 标为 `failed`。在读与写之间 Worker 可能已认领，导致旧状态覆盖 `running`。选择与认领/取消相同的数据库条件更新：只有 `WHERE status = pending` 影响一行，才写入失败状态和日志；若已认领，API 返回“状态不确定，先检查任务”的 503，不擅自失败化，也不指示立即重复提交。没有把 Redis 与数据库宣称为原子事务。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 仅在待执行时记录入队失败及日志；API 根据是否成功标记给出不同 503 指引 | `backend/app/services/runs.py::fail_pending_enqueue`、`backend/app/main.py::_enqueue_run` |
| 双线程隔离测试确认认领与失败标记互斥 | `backend/tests/test_persistence.py::PersistenceTests.test_broker_failure_and_worker_claim_cannot_both_win` |
| 模拟已认领后入队确认错误，确保 API 不覆盖运行中状态 | `backend/tests/test_api_journey.py::ApiJourneyTests.test_broker_error_does_not_overwrite_already_claimed_run` |
| 更新任务异常语义 | `docs/TASK_EXECUTION.md::状态机` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_persistence.PersistenceTests.test_broker_failure_and_worker_claim_cannot_both_win backend.tests.test_api_journey.ApiJourneyTests.test_broker_error_does_not_overwrite_already_claimed_run -q`：两项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：146 项通过。
- 使用文件型/内存型隔离 SQLite 与 mock Celery，未修改现有 OrbStack 任务或 Redis。

## 风险与未决事项

Kombu `OperationalError` 只说明调用失败，不能绝对证明消息未送达；本次用数据库当前状态避免覆盖已认领任务，但 `pending` 与实际队列之间仍可能出现确认歧义。事务发件箱、恢复扫描和 PostgreSQL 实际压力测试不在本次范围，答辩不能称“严格恰好一次投递”。
