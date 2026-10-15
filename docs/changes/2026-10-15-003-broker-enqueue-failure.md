# CHG-20261015-003：消息队列连接失败时记录可重试任务状态

- 日期：2026-10-15
- 类型：task reliability fix + API regression
- 状态：本机测试通过
- 关联提交：与本记录同次提交

## 背景与决策过程

普通、历史、多因子任务及重试入口都先提交数据库记录，再调用 Celery `apply_async`。若 Redis 连接失败，原实现让接口异常退出，但数据库 Run 留在 `pending`，用户无法从任务状态判断失败，也不能直接重试。选择集中处理 Kombu `OperationalError`：在已确认的连接错误中，将仍为 `pending` 的 Run 标为 `failed`、写入固定错误日志并返回 503。只处理这一明确类型，不对交付状态可能不确定的其他异常擅自宣称“未入队”；不在日志或响应中暴露原始连接异常。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 四个异步入口统一入队，连接失败时记录失败并返回 503 | `backend/app/main.py::_enqueue_run`、`create_task`、`create_historical_task`、`create_composite_task`、`retry_task` |
| 状态机允许待执行任务因入队故障转为失败 | `backend/app/services/runs.py::transition` |
| 隔离 API 模拟 Redis 连接失败，验证状态、日志、错误脱敏和恢复重试 | `backend/tests/test_api_journey.py::ApiJourneyTests.test_broker_connection_failure_records_failed_run_and_allows_retry` |
| 更新状态机与运维说明 | `docs/TASK_EXECUTION.md::状态机` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_api_journey.ApiJourneyTests.test_broker_connection_failure_records_failed_run_and_allows_retry -q`：通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：141 项通过。
- 测试使用内存 SQLite 和 mock Celery，不触碰现有 OrbStack 的任务或 Redis。

## 风险与未决事项

数据库提交与消息投递仍不是同一个原子事务。本修复只覆盖 Kombu 明确报告的连接故障，不等同于事务发件箱、重复投递去重或队列恢复自动补发。若消息已送达但 ACK 异常，仍需运维核对实际队列与任务日志；现有主栈未人为断开 Redis 实测。
