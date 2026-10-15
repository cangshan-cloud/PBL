# CHG-20261015-009：演示前可选活跃任务时长预检

- 日期：2026-10-15
- 类型：read-only preflight + tests + evidence
- 状态：verified on Mac OrbStack
- 关联提交：与本记录同次提交

## 背景与决策过程

Worker 运行中崩溃可能留下长期 `running` 的 Run；自动将其重置为失败存在误伤真实长计算的风险。课程演示更需要在会前发现异常并保留人工判断。选择在已有只读预检加入可选 `--max-active-age-minutes N`，从查看者可读任务列表检查 `pending.queued_at` 和 `running.started_at`，超过阈值便以任务 ID/状态/时长失败退出；默认不启用，避免正常新环境受影响。不调用取消或重试接口，也不推断 Worker 一定崩溃。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| UTC/带时区时间解析、正阈值检查、超时任务摘要及 CLI 参数 | `tools/check_demo_readiness.py::check_active_task_age`、`check_readiness`、`main` |
| 活跃/终态、带时区/无时区、缺失时间戳和只读行为回归 | `backend/tests/test_demo_readiness.py::DemoReadinessTests` |
| 演示命令、解释与实测边界 | `docs/DEMO_REHEARSAL.md::会前只读预检` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_demo_readiness -q`：12 项通过。
- 现有 Mac OrbStack `fbl` 栈只读执行 `--max-active-age-minutes 30 --require-report-fallback --check-worker --compose-project fbl`：无超时活跃任务；前端入口、三账号、数据文件、六因子、报告摘要与 Celery ping 均通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：149 项通过。

## 风险与未决事项

阈值是演示运维提示，不是 Worker 健康证明；正常长任务可能超阈值，刚崩溃任务也可能暂未超阈值。接口返回的无时区时间按 UTC 解释，与服务端当前写入口径一致。该功能不自动恢复、取消或重试任务；恢复策略、心跳与租约机制仍未实现。
