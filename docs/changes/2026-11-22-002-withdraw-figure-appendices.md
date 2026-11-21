# CHG-20261122-002：撤回独立图件附录，交付范围限定为八份中期报告

## 背景与决策过程

上一项变更 [CHG-20261122-001](2026-11-22-001-standalone-figure-appendices.md) 为四名成员各制作了一份独立图件附录。用户随后明确：“我不需要……附录，你只用给我4人对应的pbl1，pbl2中期报告就行。”因此本次按最新交付要求撤回四份附录；四人各一份 PBL1 和 PBL2 中期报告，共八份 Word，构成当前交付物。报告正文中已有的设计图和说明继续保留。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 删除四份附录 Word 及附录产物说明 | `outputs/pbl-figure-appendices-2026-11-22/` |
| 删除附录目录页及其生成、检查脚本 | `docs/PBL_FIGURE_APPENDICES_2026-11-22.md`、`tools/build_pbl_figure_appendices.py`、`tools/check_pbl_figure_appendices.py` |
| 明确八份 Word 为交付范围 | `docs/PBL_MIDTERM_REPORTS_2026-11-21.md` |
| 更新图片目录说明：设计图位于报告正文 | `docs/PBL_MIDTERM_FIGURE_CATALOG_2026-11-21.md` |
| 更新四人责任材料的交付入口 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |
| 保留撤回前决策及建立本次变更索引 | `docs/changes/2026-11-22-001-standalone-figure-appendices.md`、`docs/CHANGE_INDEX.md` |

八份原有中期报告位于 `outputs/pbl-midterm-reports-2026-11-21/final/`，本次未改动这些 Word，也未改动对应的 22 张内嵌图源文件。

## 验证结果

检查八份报告数量与结构、变更记录和 Markdown 链接；确认四份独立附录及其脚本不再存在。用户此前修改的四人分工 Excel 文件不纳入本次变更。
