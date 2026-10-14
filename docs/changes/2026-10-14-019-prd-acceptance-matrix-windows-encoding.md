# CHG-20261014-019：PRD 验收矩阵与 Windows 报告测试编码修正

- 日期：2026-10-14
- 类型：docs + fix
- 状态：implemented，本次远端 Windows CI 待验证
- 关联提交：与本记录同次提交

## 背景与目标

队长要求继续推进“PRD—实现—测试证据”对照，并核实 GitHub Actions 实际结果。公开 Actions API 显示：`8ab9252` 的运行 #38538602151 双平台后端测试失败；可选 BaoStock 测试依赖修复 `08e512b` 的运行 #38539572865 中，Ubuntu job 通过，Windows job 仍在后端测试失败。公开 job 注释仅有退出码，没有具体断言。代码审查发现历史任务测试以系统默认编码读取包含中文的 UTF-8 报告，在 Windows 常见代码页下不可靠。

## 决策过程

矩阵不以代码存在代替验收，分别标注本机、CI、目标环境和个人署名证据。对 Windows 测试，选择在文件边界显式指定 UTF-8 并复用一次读取结果；不通过在 CI 中强制全局 UTF-8 来掩盖其他跨平台问题。此修正是有证据的候选原因，尚不能仅凭本机测试断言它就是远端唯一失败原因。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 对照 PRD 关键功能、实现、测试、缺口和放行门槛 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md::功能与验收矩阵`、`自动化与环境证据`、`下一步顺序与放行门槛` | 第一次汇报和范围控制的事实底稿；无新增产品功能 |
| 历史报告测试显式按 UTF-8 解码 | `backend/tests/test_historical_task.py::HistoricalTaskTests.test_dedicated_task_produces_metrics_report_and_audit` | 避免依赖 Windows 系统默认代码页 |
| 增加文档入口 | `README.md::当前阶段边界` | 便于团队找到最新差距表 |
| 登记本次修改 | `docs/CHANGE_INDEX.md` 对应条目 | 保留决策与证据 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：129 项通过。
- 模拟 `Path.read_text()` 默认使用 `cp1252`，单独执行历史任务测试：2 项通过；显式指定 UTF-8 的读取不受默认编码影响。
- `.venv/bin/python tools/verify_golden_research.py`：通过；上一轮前端生产构建通过，本次未改前端。
- GitHub Actions：本次提交尚未推送／运行；以运行结束后的记录为准。

## 风险、回退与未决事项

若 Windows CI 仍失败，须继续定位具体测试，不能将“编码修正”写成已解决。矩阵同时揭示 Parquet/DuckDB、中性化、服务端 PDF、页面延迟指标和 Windows 离线部署等未闭合项；这些缺口需要课程要求决策或补充验收，不能因文档完成而自动销项。
