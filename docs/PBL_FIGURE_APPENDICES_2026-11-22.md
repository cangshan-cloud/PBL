# 四人设计图件附录总索引

本批图件附录按 M1—M4 功能模块分别编制，可作为四人个人报告的独立附件，也可按页抽取图片和图注用于答辩。每页只有一张设计图，附图种、建议放置章节、图意、代码依据和验收提示。图件说明的是当前软件设计和可执行的验收口径；它们不是运行截图、真实收益图或成员本人操作记录。

| 成员 | 模块 | 独立 Word 附录 | 图数与页数 | 主要内容 |
| --- | --- | --- | --- | --- |
| A | M1 平台基础与任务运行 | [A 设计图件附录](../outputs/pbl-figure-appendices-2026-11-22/final/A_平台基础与任务运行_设计图件附录.docx) | 10 图，10 页 | 部署、状态机、时序、协作、授权、恢复、故障分支、领域模型、权限矩阵与交付流程 |
| B | M2 数据集管理与质量控制 | [B 设计图件附录](../outputs/pbl-figure-appendices-2026-11-22/final/B_数据集管理与质量控制_设计图件附录.docx) | 4 图，4 页 | 质量门禁、版本血缘、生命周期与发布决策 |
| C | M3 因子计算与研究检验 | [C 设计图件附录](../outputs/pbl-figure-appendices-2026-11-22/final/C_因子计算与研究检验_设计图件附录.docx) | 4 图，4 页 | 信号收益对齐、指标复算、依赖关系与截面有效性 |
| D | M4 研究工作台与报告交付 | [D 设计图件附录](../outputs/pbl-figure-appendices-2026-11-22/final/D_研究工作台与报告交付_设计图件附录.docx) | 4 图，4 页 | 同 Run 交付、请求身份、页面架构与页面状态 |

原始独立 PNG 与代码依据见[中期报告图册](PBL_MIDTERM_FIGURE_CATALOG_2026-11-21.md)；八份已嵌图的中期报告见[中期报告总索引](PBL_MIDTERM_REPORTS_2026-11-21.md)。Word 附录采用 A4 横向、一图一页，便于直接打印或插入其他材料。四份附录不包含姓名、学号等未提供的个人信息，封面使用成员 A/B/C/D 标识。

生成器为 [`tools/build_pbl_figure_appendices.py`](../tools/build_pbl_figure_appendices.py)，结构检查为 [`tools/check_pbl_figure_appendices.py`](../tools/check_pbl_figure_appendices.py)。四份 Word 均经逐页渲染检查。创建和排版决策见 [CHG-20261122-001](changes/2026-11-22-001-standalone-figure-appendices.md)。
