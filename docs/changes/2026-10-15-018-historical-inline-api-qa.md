# CHG-20261015-018：历史包修正后的隔离 API 端到端复测

- 日期：2026-10-15
- 类型：evidence-only / isolated private-bundle API QA
- 状态：verified on Mac inline API; Compose queue not rerun
- 关联提交：与本记录同次提交（无应用代码修改）

## 背景与决策过程

CHG-20261015-017 修正了历史包加载时的字节复验，但只读加载和单元测试不能证明新源码仍可经 API 完成任务、报告与审计下载。原有写入式验收脚本要求独立 Compose 栈；本轮沙箱访问 OrbStack Docker socket 被拒绝。为不污染现有 `fbl` 演示数据库，选择在进程内使用独立内存 SQLite、FastAPI TestClient、inline 任务执行与自动清理的临时报告目录，种入指向本机已封存私有包的**隔离数据库记录**，走实际登录、历史任务创建与四个 HTTP 下载接口；不假称验证 Celery/Compose。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 记录隔离 API 任务、四份产物及边界 | `docs/HS300_BUNDLE.md` |
| 更新 PRD 验收证据 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 登记本次证据 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- 本机私有包 ID `hs300_2024_0375298bd2c8ac52`，清单 SHA-256 `29e09ea82da9c15fcd8c7ebb2d3c99fd795df82312f6e2b431301ce2efd676d5`。
- 研究员经真实 FastAPI `/auth/login`，再经 `/research/historical-tasks` 新建 inline 任务 `63189247-5abd-4aec-a6ea-7ff6d8973eaf`：HTTP 201、`success`、组合有效观测 72,366。
- 四份下载均 HTTP 200；`tools/verify_historical_audit_exports.py::verify_exports` 核对：4 因子、968 行逐日审计、32 条无标签信号、HTML 报告 SHA-256 匹配。
- 内存数据库和临时输出随进程退出清理；未写入现有 `fbl` 数据库，未改动私有包。`git diff --check` 通过。

## 风险与未决事项

测试绕过了包注册 API（在隔离库中种入已发布包记录），但研究任务及四份下载均通过真实 API 路由。它使用 inline 而非 Celery Worker，不覆盖 Compose 队列、真实浏览器、Windows 部署或源数据许可。若要复测容器队列，应使用独立 Compose 项目和已有 `tools/verify_historical_api_journey.py`，不能指向现有演示库。本次文档提交的 CI 需另查。
