# CHG-20261015-005：数据库条件认领待执行研究任务

- 日期：2026-10-15
- 类型：worker concurrency fix + regression
- 状态：本机测试通过
- 关联提交：与本记录同次提交

## 背景与决策过程

上一轮仅在执行入口读取 `Run.status`，再普通更新为 `running`；两个 Worker 若同时读到 `pending`，都可能开始计算。为避免同一 Run 的并发重复计算，选择使用数据库条件更新 `WHERE id = ? AND status = pending`，只有影响一行的执行者取得认领权。`running` 的时间、进度与一条 `started` 日志在同一数据库事务中提交。未认领者只返回当前 Run，不进入因子计算。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 条件更新状态并同事务记录开始日志，执行入口先取得认领权 | `backend/app/services/runs.py::claim_pending_run`、`execute_research_run` |
| 两个独立 Session 同时争抢，断言仅一个成功及一条开始日志 | `backend/tests/test_persistence.py::PersistenceTests.test_two_workers_can_claim_a_pending_run_only_once` |
| 更新并发语义与剩余限制 | `docs/TASK_EXECUTION.md::状态机` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_persistence.PersistenceTests.test_two_workers_can_claim_a_pending_run_only_once -q`：双线程、文件型 SQLite 隔离并发测试通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：143 项通过。
- 未向现有 OrbStack 栈投递任务；PostgreSQL 实际并发压测尚未执行。

## 风险与未决事项

本次保证单条 Run 在数据库条件更新下最多被一个 Worker 从 `pending` 认领，不保证业务任务“恰好完成一次”。Worker 崩溃后停留在 `running` 的恢复、Redis 投递确认与数据库原子性、取消与认领同时发生时的更细协调仍需另行设计和验收。本机 SQLite 并发测试不能替代目标 PostgreSQL 压测。
