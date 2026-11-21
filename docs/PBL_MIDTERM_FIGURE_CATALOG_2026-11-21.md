# PBL 中期报告图册与使用说明

本图册与 [四人中期报告总索引](PBL_MIDTERM_REPORTS_2026-11-21.md)配套。以下 PNG 均已嵌入对应报告，也可单独用于汇报、答辩或附录。图中展示的是软件设计与当前仓库实现关系，不是实际交易或收益图；引用时保留图题和下表的代码依据。

| 成员 | 图件 | 建议图题与说明 | 代码或配置依据 |
| --- | --- | --- | --- |
| A | [五服务部署与数据流](../outputs/pbl-midterm-reports-2026-11-21/assets/A_platform_architecture.png) | Web、API、Worker、PostgreSQL、Redis 的职责及研究结果保存位置 | `docker-compose.yml`、`backend/app/tasks.py`、`backend/app/models.py` |
| A | [Run 状态机](../outputs/pbl-midterm-reports-2026-11-21/assets/A_run_state_machine.png) | pending、running 与三个终态；取消请求和条件认领边界 | `backend/app/models.py::RunStatus`、`backend/app/services/runs.py::transition`、`claim_pending_run` |
| A | [异步研究任务时序](../outputs/pbl-midterm-reports-2026-11-21/assets/A_async_sequence.png) | 提交、保存与入队、立即返回 Run ID、Worker 认领和结果写回 | `backend/app/main.py::create_task`、`backend/app/tasks.py::execute_research_run_task` |
| A | [四模块集成契约](../outputs/pbl-midterm-reports-2026-11-21/assets/A_module_integration.png) | 数据版本、Run 参数快照、结构化结果与同 Run 交付的顺序 | `docs/TEAM_MODULE_DIVISION_2026-11-20.md`、`backend/app/models.py` |
| A | [后端授权检查路径](../outputs/pbl-midterm-reports-2026-11-21/assets/A_permission_path.png) | 身份、角色、Run 归属和派生产物访问的检查顺序 | `backend/app/main.py`、`backend/app/models.py` |
| A | [故障恢复核对顺序](../outputs/pbl-midterm-reports-2026-11-21/assets/A_recovery_path.png) | 服务、迁移、数据库、旧 Run 和新任务的恢复验收 | `docker-compose.yml`、`backend/app/services/runs.py` |
| A | [异步任务故障分支](../outputs/pbl-midterm-reports-2026-11-21/assets/A_task_failure_branches.png) | 入队失败、重复投递和执行异常分段处理 | `backend/app/services/runs.py`、`backend/app/tasks.py` |
| A | [研究任务领域模型](../outputs/pbl-midterm-reports-2026-11-21/assets/A_domain_model.png) | 用户、数据版本、实验、运行、日志和产物的关联 | `backend/app/models.py` |
| A | [角色与资源权限矩阵](../outputs/pbl-midterm-reports-2026-11-21/assets/A_role_matrix.png) | 管理员、研究员、查看者的写入与读取边界 | `backend/app/main.py`、`backend/app/auth.py` |
| A | [组长交付放行流程](../outputs/pbl-midterm-reports-2026-11-21/assets/A_release_gate.png) | 代码冻结、回归、部署、材料和人工核对 | `docs/TEAM_MODULE_DIVISION_2026-11-20.md`、`docs/CHANGE_INDEX.md` |
| B | [数据版本质量门禁](../outputs/pbl-midterm-reports-2026-11-21/assets/B_data_quality_gate.png) | 导入与来源、字段校验、哈希、无阻断错误后发布 | `backend/app/services/datasets.py::import_csv`、`publish_dataset_version` |
| B | [数据版本血缘](../outputs/pbl-midterm-reports-2026-11-21/assets/B_version_lineage.png) | 从来源、质量摘要和 SHA-256 到已发布版本及 Run 引用 | `backend/app/services/datasets.py`、`backend/app/models.py` |
| B | [数据版本生命周期](../outputs/pbl-midterm-reports-2026-11-21/assets/B_dataset_lifecycle.png) | draft、发布门禁和 published 的转换与阻断分支 | `backend/app/services/datasets.py::import_csv`、`publish_dataset_version` |
| B | [数据发布质量决策树](../outputs/pbl-midterm-reports-2026-11-21/assets/B_quality_decision.png) | 结构错误与业务阻断分别拒绝并留下原因 | `backend/app/services/datasets.py::validate_csv`、`publish_dataset_version` |
| C | [信号与下一期收益对齐](../outputs/pbl-midterm-reports-2026-11-21/assets/C_signal_return_alignment.png) | 信号日、预处理、收益标签、共同样本与逐日 IC | `backend/app/domain/research.py::evaluate`、`backend/app/domain/historical_research.py` |
| C | [研究指标独立复算链](../outputs/pbl-midterm-reports-2026-11-21/assets/C_research_audit.png) | 从参数、逐股观测、逐日指标到汇总和报告的核对次序 | `backend/app/domain/research.py`、`tools/verify_historical_audit_exports.py` |
| C | [指标依赖关系图](../outputs/pbl-midterm-reports-2026-11-21/assets/C_metric_dependencies.png) | 共同样本分流至 IC、分组、成本和汇总 | `backend/app/domain/research.py::evaluate` |
| C | [逐日截面有效性决策](../outputs/pbl-midterm-reports-2026-11-21/assets/C_valid_slice_decision.png) | 样本数和方差不足时保留跳过原因 | `backend/app/domain/research.py::evaluate` |
| D | [同 Run 的页面与交付](../outputs/pbl-midterm-reports-2026-11-21/assets/D_run_delivery_identity.png) | 配置、任务回看、诊断、报告与多格式导出 | `frontend/src/main.tsx`、`backend/app/services/reports.py` |
| D | [页面请求身份守护](../outputs/pbl-midterm-reports-2026-11-21/assets/D_request_identity.png) | 切换 Run 后忽略迟到响应并保持下载目标一致 | `frontend/src/main.tsx` |
| D | [研究工作台页面架构](../outputs/pbl-midterm-reports-2026-11-21/assets/D_workspace_map.png) | 配置、任务、诊断、报告和下载的导航关系 | `frontend/src/main.tsx` |
| D | [任务页面状态机](../outputs/pbl-midterm-reports-2026-11-21/assets/D_ui_state_machine.png) | 未选择、pending、running 与三种终态的页面行为 | `frontend/src/main.tsx`、`backend/app/models.py::RunStatus` |

每份报告还保留一张与个人模块对应的原流程图，位于同一 [`assets/`](../outputs/pbl-midterm-reports-2026-11-21/assets/) 目录，文件名格式为 `{成员}_pbl1_midterm_diagram.png` 或 `{成员}_pbl2_midterm_diagram.png`。因此 A 的 PBL1 有 7 张正文图、PBL2 有 6 张正文图；B/C/D 的两份报告各有 4 张正文图。以上数量不计模板封面校徽。图册表格共 22 张独立 PNG，每份报告只嵌入对应课程和模块的图。

图件由 [`tools/build_pbl_midterm_figures.py`](../tools/build_pbl_midterm_figures.py)以 1800×720 像素生成，可重复修改文字与配色；Word 成品由 [`tools/build_pbl_midterm_reports.py`](../tools/build_pbl_midterm_reports.py)统一嵌入。不要把设计流程图称为真实产品截图或实际运行日志。
