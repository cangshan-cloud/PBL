# CHG-20261025-001 当前历史任务私有包隔离复算正例

## 问题与决策

上一轮只读复算发现 2026-10-14 旧导出与当前研究口径不一致；合成单测的正例不足以证明当前真实私有包能从任务结果回到同一结果。决定新增受控的本机隔离运行入口：只在内存 SQLite 中创建当前历史任务，报告写临时目录，派生证据仅落在 Git 忽略的 `data/real/` 新目录；导出后立即核对报告摘要和当前源码复算。拒绝公开目录、已存在目录及无显式确认的调用。实际执行者：Codex。

## 修改内容与位置

- `tools/run_isolated_historical_replay.py::require_private_new_output`、`run_isolated_replay`、`main`：内存库生成当前历史任务和两份私有派生证据，并串行复核。
- `backend/tests/test_isolated_historical_replay.py`：验证私有新目录限定、已有目录拒绝及显式确认门槛。
- `docs/HISTORICAL_CURRENT_REPLAY_2026-10-25.md`：记录任务 ID、摘要、命令和研究边界；不链接私有文件。
- `docs/HS300_BUNDLE.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：更新当前源码新任务正例与旧导出区分。

## 验证与边界

本机私有包任务 `3a559947-e620-48f2-b00c-af57473e056f` 成功，四因子共同观测 72,366；新复现 JSON 与 HTML 报告摘要通过，离线复算工具对落盘文件再次通过。产物仅在被忽略的 `data/real/current_replay_2026-10-24/`；`git check-ignore` 确认目录受忽略。安全门槛定向 2 项、项目虚拟环境后端全量 276 项、黄金手算核对及变更台账 209 条索引/47 条近期 A/B/C/D 链接均通过；远端 CI 待提交后核对。工具不接触既有主栈数据库，不证明独立公式、行情授权或可成交收益；未做 Celery/容器/浏览器互动及队长本人实测。分工 Excel 保持原样。
