# CHG-20261015-006：取消与 Worker 认领的条件更新协调

- 日期：2026-10-15
- 类型：task concurrency fix + regression
- 状态：本机测试通过
- 关联提交：与本记录同次提交

## 背景与决策过程

Worker 已用数据库条件更新认领 `pending`，但取消接口仍基于先前读到的 ORM 状态调用普通 `transition`。取消与认领并发时，旧状态可能覆盖新状态。选择将取消也改为条件更新：先尝试 `pending → cancelled`，失败则尝试给 `running` 写入一次取消请求；二者都失败时重新读取当前终态并按原权限/错误语义返回。每个成功更新与对应日志在同一事务提交，不创建新任务。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 取消、运行中取消请求的条件更新及日志 | `backend/app/services/runs.py::request_cancellation` |
| 文件型 SQLite 双线程同时取消/认领，验证两种合法结果；原有取消测试保留 | `backend/tests/test_persistence.py::PersistenceTests.test_cancellation_and_worker_claim_have_one_consistent_outcome` |
| 更新并发取消说明 | `docs/TASK_EXECUTION.md::取消语义` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_persistence.PersistenceTests.test_cancellation_and_worker_claim_have_one_consistent_outcome -q`：双线程并发测试通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：144 项通过。
- 未操作现有 OrbStack 任务，也未在真实 PostgreSQL 上做取消/认领并发压测。

## 风险与未决事项

条件更新只协调同一数据库中取消与认领的先后，不会中断正在进行的单个同步计算步骤。Worker 崩溃后 `running` 悬留、Redis 投递不确定性和 PostgreSQL 实际压力场景仍未解决。本次不改变终态任务不可取消的规则。
