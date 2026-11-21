# PBL 中期报告图册与使用说明

本图册与 [四人中期报告总索引](PBL_MIDTERM_REPORTS_2026-11-21.md)配套。以下 PNG 均已嵌入对应报告，也可单独用于汇报、答辩或附录。图中展示的是软件设计与当前仓库实现关系，不是实际交易或收益图；引用时保留图题和下表的代码依据。

| 成员 | 图件 | 建议图题与说明 | 代码或配置依据 |
| --- | --- | --- | --- |
| A | [五服务部署与数据流](../outputs/pbl-midterm-reports-2026-11-21/assets/A_platform_architecture.png) | Web、API、Worker、PostgreSQL、Redis 的职责及研究结果保存位置 | `docker-compose.yml`、`backend/app/tasks.py`、`backend/app/models.py` |
| A | [Run 状态机](../outputs/pbl-midterm-reports-2026-11-21/assets/A_run_state_machine.png) | pending、running 与三个终态；取消请求和条件认领边界 | `backend/app/models.py::RunStatus`、`backend/app/services/runs.py::transition`、`claim_pending_run` |
| A | [异步研究任务时序](../outputs/pbl-midterm-reports-2026-11-21/assets/A_async_sequence.png) | 提交、保存与入队、立即返回 Run ID、Worker 认领和结果写回 | `backend/app/main.py::create_task`、`backend/app/tasks.py::execute_research_run_task` |
| A | [四模块集成契约](../outputs/pbl-midterm-reports-2026-11-21/assets/A_module_integration.png) | 数据版本、Run 参数快照、结构化结果与同 Run 交付的顺序 | `docs/TEAM_MODULE_DIVISION_2026-11-20.md`、`backend/app/models.py` |
| B | [数据版本质量门禁](../outputs/pbl-midterm-reports-2026-11-21/assets/B_data_quality_gate.png) | 导入与来源、字段校验、哈希、无阻断错误后发布 | `backend/app/services/datasets.py::import_csv`、`publish_dataset_version` |
| C | [信号与下一期收益对齐](../outputs/pbl-midterm-reports-2026-11-21/assets/C_signal_return_alignment.png) | 信号日、预处理、收益标签、共同样本与逐日 IC | `backend/app/domain/research.py::evaluate`、`backend/app/domain/historical_research.py` |
| D | [同 Run 的页面与交付](../outputs/pbl-midterm-reports-2026-11-21/assets/D_run_delivery_identity.png) | 配置、任务回看、诊断、报告与多格式导出 | `frontend/src/main.tsx`、`backend/app/services/reports.py` |

每份报告还保留一张与个人模块对应的原流程图，位于同一 [`assets/`](../outputs/pbl-midterm-reports-2026-11-21/assets/) 目录，文件名格式为 `{成员}_pbl1_midterm_diagram.png` 或 `{成员}_pbl2_midterm_diagram.png`。因此 A 的 PBL1 有 4 张正文图、PBL2 有 3 张正文图；B/C/D 的两份报告各有 2 张正文图。以上数量不计模板封面校徽。

图件由 [`tools/build_pbl_midterm_figures.py`](../tools/build_pbl_midterm_figures.py)以 1800×720 像素生成，可重复修改文字与配色；Word 成品由 [`tools/build_pbl_midterm_reports.py`](../tools/build_pbl_midterm_reports.py)统一嵌入。不要把设计流程图称为真实产品截图或实际运行日志。
