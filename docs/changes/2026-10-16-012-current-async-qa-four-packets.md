# CHG-20261016-012：当前版本异步链路与四责任包同步验收

- 日期：2026-10-16
- 类型：isolated Compose QA + reproducibility check + team evidence
- 状态：verified on Mac；Windows and timed browser rehearsal pending
- 关联提交：与本记录同次提交

## 背景与决策过程

上一轮浏览器技术彩排使用 inline 模式，主 OrbStack 镜像又早于当前代码，不能证明本版 API→Redis→Celery Worker。队长进一步约定以后每次测试同步完成 A/B/C/D 四责任包材料、无需成员本人签收，并将自己的产品实测数据后补。决定以准确命名的独立 Compose 项目构建当前 API/Worker，独立数据库卷和临时报告目录，演示 CSV 只读挂载；先核对合并配置再启动。异步脚本原只检查任务、报告目录摘要，故补复现 JSON 的任务、结果和双摘要核对及纯函数回归。四份材料写明“开发者代执行”，不冒称成员个人贡献。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 复现包结果／报告摘要核对 | `tools/verify_compose_stack.py::verify_snapshot`、`main` | 每次异步烟测涵盖 JSON 与 HTML 出口 |
| 正常与篡改回归 | `backend/tests/test_compose_stack_verify.py` | 结果或报告变化被拒绝 |
| 本轮隔离运行记录 | `docs/ASYNC_ACCEPTANCE_2026-10-16.md`、`docs/ORBSTACK_DEPLOYMENT.md` | 保存项目、任务 ID、Worker 与限制 |
| 新的四责任包执行约定 | `docs/TEAM_PLAN.md`、`docs/DEMO_REHEARSAL.md`、`docs/FINAL_REHEARSAL_CHECKLIST.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/DEV_REHEARSAL_2026-10-16.md` | 不再要求成员个人签收，始终标实际执行者；历史彩排标明新约定 |
| A/B/C/D 本轮验收 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` | 每个责任包有本轮结果与未覆盖项 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯本次决策 |

## 验证与结果

- Compose 合并配置核对项目名 `factorlab-async-qa-1016`、仅 loopback `18002` API、只读 `data/sample` 和临时运行目录；隔离 db/redis/api/worker 健康，宿主机 API HTTP 200，迁移 `20261010_0004 (head)`。
- 原脚本任务 `5e6855f7-d74c-44af-915c-8b52b4310dde` 成功；增强脚本任务 `c6f2dc2e-a40a-465e-84ac-31d4fa286716` 成功，Worker 日志显示接收与完成，99 个有效 IC 日、五组各 99 点，目录及复现双摘要通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：185 项通过；`tools/verify_golden_research.py`、`tools/verify_real_a_share_sample.py`、`npm run build --prefix frontend`：通过。
- 用精确项目名执行 `docker compose down`；移除测试容器和网络，保留专用数据库卷及临时报告证据，主 `fbl` 服务仍在。
- `git diff --check`：见提交前检查。

## 风险、回退与未决事项

本轮未重做前端浏览器或十分钟正式连续计时；页面证据引用上一轮隔离彩排。真实 10 股样本回归仍不是来源许可认证。Windows 未验，最新 GitHub CI 须按提交独立核对。验收项目是专用资源，可用精确项目名停止；不得对主 `fbl` 栈执行 `down -v`。如果清理专用数据库卷，须先确认不再需要其任务记录。
