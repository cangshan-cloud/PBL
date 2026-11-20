# 四人 PBL 中期报告总索引（2026-11-21）

## 1. 使用说明

本批材料依据教师提供的 PBL1、PBL2 中期报告模板制作，并沿用 [`TEAM_MODULE_DIVISION_2026-11-20.md`](TEAM_MODULE_DIVISION_2026-11-20.md) 的 M1—M4 功能模块分工。四人各有一份 PBL1 和一份 PBL2 中期报告，共 8 份独立 Word 文档；教师提纲与评分表保留，正文按共同项目内容和个人模块内容分别填写。

姓名、学号、班级、任课教师尚未确认，封面统一保留 `【待填写：……】` 占位符。正式提交前应填写基础信息，并用实际提交软件快速检查分页和文件名。

## 2. 模板要求映射

| 报告 | 模板要求 | 本批实现 |
| --- | --- | --- |
| PBL1 | 项目概述、技术架构、技术实现、项目进度、挑战与学习、未来计划、相关代码 | 共同概述与架构；个人模块实现、接口、进展、挑战、学习、计划；附架构/处理链图和真实代码节选 |
| PBL2 | 项目概述、需求分析、功能设计、挑战与问题、下一步计划；有代码时附代码 | 共同概述与需求；个人功能流程、需求/验收表、算法与接口、挑战、计划；附业务流程图和真实代码节选 |

报告中的“已完成”以现有自动化或开发者代执行证据为依据，不写成成员本人已完成最终人工产品验收。平台仅用于课程研究，不连接真实资金账户，研究结果不构成投资建议。

## 3. 八份成品

| 成员占位 | 功能模块 | PBL1 | PBL2 |
| --- | --- | --- | --- |
| A【队长姓名】 | M1 平台基础与任务运行 | [`A_平台基础与任务运行_PBL1_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/A_平台基础与任务运行_PBL1_中期报告.docx) | [`A_平台基础与任务运行_PBL2_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/A_平台基础与任务运行_PBL2_中期报告.docx) |
| B【成员姓名】 | M2 数据集管理与质量控制 | [`B_数据集管理与质量控制_PBL1_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/B_数据集管理与质量控制_PBL1_中期报告.docx) | [`B_数据集管理与质量控制_PBL2_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/B_数据集管理与质量控制_PBL2_中期报告.docx) |
| C【成员姓名】 | M3 因子计算与研究检验 | [`C_因子计算与研究检验_PBL1_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/C_因子计算与研究检验_PBL1_中期报告.docx) | [`C_因子计算与研究检验_PBL2_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/C_因子计算与研究检验_PBL2_中期报告.docx) |
| D【成员姓名】 | M4 研究工作台与报告交付 | [`D_研究工作台与报告交付_PBL1_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/D_研究工作台与报告交付_PBL1_中期报告.docx) | [`D_研究工作台与报告交付_PBL2_中期报告.docx`](../outputs/pbl-midterm-reports-2026-11-21/final/D_研究工作台与报告交付_PBL2_中期报告.docx) |

## 4. 个人内容边界

| 模块 | PBL1 个人重点 | PBL2 个人重点 | 代码节选位置 |
| --- | --- | --- | --- |
| M1 | RBAC、Run 状态、Celery、持久化、部署与审计 | 异步任务业务流、状态约束、任务验收 | `backend/app/tasks.py` |
| M2 | CSV/历史包、版本、SHA-256、质量门禁与授权边界 | 数据导入发布流、质量算法、接口和异常用例 | `backend/app/services/datasets.py::import_csv` |
| M3 | 因子、预处理、IC/Rank IC、分组、成本与独立审计 | 信号—收益对齐、共同样本和研究检验算法 | `backend/app/domain/research.py::evaluate` |
| M4 | 工作台、任务回看、图表诊断、报告与多格式导出 | 配置—执行—回看—交付流程和 Run 身份核对 | `frontend/src/main.tsx::downloadReport` |

## 5. 生成与核验

- 生成脚本：`tools/build_pbl_midterm_reports.py`
- 结构检查：`tools/check_pbl_midterm_reports.py`
- 模板转换件：`outputs/pbl-midterm-reports-2026-11-21/templates-converted/`
- 图形资产：`outputs/pbl-midterm-reports-2026-11-21/assets/`
- 最终 Word：`outputs/pbl-midterm-reports-2026-11-21/final/`
- 模板哈希、版式和填充约定：`outputs/pbl-midterm-reports-2026-11-21/artifact.md`

8 份文档均已通过 DOCX ZIP 完整性、数量、标题、模块、占位符、章节、图形、代码位置和最低内容量检查，并逐页渲染复核。PBL1 总页数均为 10 页，PBL2 总页数均为 11 页；页数包含模板封面、提纲和评分表。
