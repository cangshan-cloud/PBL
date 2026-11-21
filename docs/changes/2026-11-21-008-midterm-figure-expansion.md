# CHG-20261121-008 中期报告多类型图件扩充

## 1 变更背景

用户要求制作更多可提交物图，用流程图、状态机和架构图丰富四人的个人中期报告。上一版图册有 12 张独立 PNG，部分报告只有三张正文图。本轮在既有模块边界和代码依据上扩充图件，并同步更新八份 Word。

## 2 决策过程

1. 组长 A 增加异步任务故障分支、研究任务领域模型、角色权限矩阵和交付放行流程四张图，覆盖平台可靠性、持久化、授权和团队组织四个不同问题。PBL1 放前两张，PBL2 放后两张。
2. B 增加数据版本生命周期和发布质量决策树；C 增加研究指标依赖图和逐日截面有效性决策图；D 增加工作台页面架构和任务页面状态图。每人 PBL1/PBL2 各嵌入对应一张，不重复堆放同一流程。
3. 每张图在报告内配有图题和解释，图册列出代码依据。图中只有设计与验收口径，不把设计图称作实机截图或真实研究收益。
4. A/C/D 的代码节选补充关键行与验收观察，使报告末页具有可讲述的设计和测试对应关系。生成器移除末尾表格后的空段落，避免产生空白尾页。
5. 保留教师模板结构和身份占位符；没有修改应用业务代码。用户已有 Excel 工作簿改动未触及。

## 3 修改位置

| 内容 | 对应位置 |
| --- | --- |
| 十张新增设计图 | `tools/build_pbl_midterm_figures.py::task_failure_branches`、`domain_model`、`role_matrix`、`release_gate`、`dataset_lifecycle`、`quality_decision`、`metric_dependencies`、`valid_slice_decision`、`workspace_map`、`ui_state_machine`；`outputs/pbl-midterm-reports-2026-11-21/assets/` |
| 嵌入图、解释文字和末页代码说明 | `tools/build_pbl_midterm_reports.py::build_pbl1`、`build_pbl2`、`add_other_code_explanation`、`build_document` |
| 图题、图片数量和结构门禁 | `tools/check_pbl_midterm_reports.py::FIGURE_ASSETS`、`NEW_CAPTIONS`、`main` |
| 八份 Word 和模板执行说明 | `outputs/pbl-midterm-reports-2026-11-21/final/`、`outputs/pbl-midterm-reports-2026-11-21/artifact.md` |
| 图册、报告总索引及四人责任材料 | `docs/PBL_MIDTERM_FIGURE_CATALOG_2026-11-21.md`、`docs/PBL_MIDTERM_REPORTS_2026-11-21.md`、`docs/member-deliverables/` |

## 4 验证结果

- 生成脚本产出 22 张独立 PNG 与八份 DOCX；每份报告有相应新增图题。结构检查验证 A 的 PBL1/PBL2 分别有 8/7 张内嵌图（含模板校徽），B/C/D 各有 5 张。
- 使用打包 LibreOffice 和临时 PingFang 字体重新渲染八份文档并逐页查看。最终页数：A 为 21/20 页，B/C/D 两份均为 17 页。移除表格末尾空段落后，A PBL1 的空白尾页消失；未见图文重叠、裁切或空白正文页。
- 文档结构检查、变更台账检查、Markdown 本地链接检查及 Git 差异空白检查通过。上述是材料完整性与排版验证，不能代替队长的最终人工产品验收。

## 5 未决事项

提交前仍须填入四人姓名、学号、班级和教师信息，并在最终使用的 Word/WPS 环境复核分页。对外汇报时可使用独立 PNG，但应注明其为软件设计图。
