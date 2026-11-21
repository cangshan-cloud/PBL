# CHG-20261121-004 中期报告图件与组长可提交物

## 变更概述

在已扩写的四人中期报告上新增 7 张独立可提交 PNG 图，并嵌入 8 份 Word 报告。A 作为组长新增五服务部署图、Run 状态机、异步任务时序图和四模块集成契约图；B/C/D 分别新增数据质量门禁、信号与收益对齐、同 Run 页面与交付图。报告原有的个人流程图继续保留。

## 决策过程

1. 用户要求更多可提交图件，尤其是组长，因此 A 的图覆盖架构、执行、状态和协作四个不同层面；其他成员各补一张最能说明模块口径的关键图。
2. 每张图由可重复运行的本地脚本生成，独立 PNG 与 Word 嵌入图使用同一来源，后续修改无需手工重画两份。
3. 图题解释输入、输出和限制，并附仓库代码或配置位置；流程图只说明设计与实现关系，不冒充真实界面截图或运行证据。
4. 状态机按实际 `RunStatus` 使用 `success`，运行中取消先记录请求再由 Worker 响应；时序图将 API 立即返回放在 Worker 后续执行之前。
5. 排版中保留图片与图题同页，并让表格行不可拆分；去除 PBL1 概述与架构之间造成大片空白的强制分页。

## 修改内容与对应位置

- 图件生成：`tools/build_pbl_midterm_figures.py` 的 `architecture`、`state_machine`、`sequence`、`integration` 和 `pipeline`。
- Word 生成：`tools/build_pbl_midterm_reports.py` 的 `add_report_figure`、`build_pbl1`、`build_pbl2`、`keep_row_together` 与 `EXTENDED["A"]["models"]`。
- 成品检查：`tools/check_pbl_midterm_reports.py` 的图件数量与独立资产检查。
- 图件索引：`docs/PBL_MIDTERM_FIGURE_CATALOG_2026-11-21.md`；报告总索引：`docs/PBL_MIDTERM_REPORTS_2026-11-21.md`。
- 独立 PNG 与 8 份更新后的 Word：`outputs/pbl-midterm-reports-2026-11-21/assets/`、`final/`。
- A/B/C/D 四份模块责任材料中追加本批图件链接。

本次未修改业务运行代码、API、数据库迁移或研究算法。

## 验证结果

- 七张新增 PNG 均为 1800×720，逐张检查文字、箭头与截断；每份报告的嵌入图数量经 DOCX 结构检查。
- 八份 Word 使用中文字体逐页渲染：A 的 PBL1/PBL2 各 14 页，B/C/D 的 PBL1/PBL2 各 12 页；图片与图题未拆开，表格行未跨页断裂。
- 图件文字与 `RunStatus`、任务认领、Compose 五服务和模块分工对照；文档索引及相对链接检查通过。

## 未决事项与限制

- 封面姓名、学号、班级和任课教师仍为待填写占位符。
- 图件是系统设计说明，无法代替队长最终实机产品操作截图；若课程要求实机截图，应从当时运行的页面单独采集并标明日期与 Run ID。
- 本批构图以 Mac 的 PingFang 字体生成 PNG；在 Word/WPS 打开报告时仍需提交前快速检查页码与图题。
