# CHG-20261015-004：延迟与重复队列消息的非待执行任务保护

- 日期：2026-10-15
- 类型：worker reliability fix + regression
- 状态：本机测试通过
- 关联提交：与本记录同次提交

## 背景与决策过程

上一轮在入队连接失败时可把待执行 Run 标为失败。若消息实际上晚到，`execute_research_run` 会直接尝试 `failed → running`，抛出状态机异常；已成功或取消任务的重复消息也一样。选择在执行入口先判断状态：只有 `pending` 进入计算，其他状态原样返回。保留 `transition` 对非法状态转换的严格约束，不通过放宽状态机允许终态复活。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 非 `pending` Run 在执行入口只读返回 | `backend/app/services/runs.py::execute_research_run` |
| 成功、失败、取消、运行中的串行晚到消息不重复计算或记日志 | `backend/tests/test_persistence.py::PersistenceTests.test_late_or_duplicate_delivery_does_not_reexecute_nonpending_run` |
| 明确串行保护和并发边界 | `docs/TASK_EXECUTION.md::状态机` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_persistence.PersistenceTests.test_late_or_duplicate_delivery_does_not_reexecute_nonpending_run -q`：通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：142 项通过。
- 使用本地隔离 SQLite 与仓库演示数据，不向现有 OrbStack 栈投递任务。

## 风险与未决事项

这是串行晚到/重投递保护，不是数据库条件更新式的原子任务认领。若两个 Worker 同时从 `pending` 开始，目前仍可能重复计算；也未实现运行中 Worker 崩溃后的自动接管。报告与任务记录仍须按既有哈希和版本约束复核。
