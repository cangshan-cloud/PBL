# CHG-20261121-007 中期报告设计图与代码验收说明

## 1 变更背景

用户希望继续优化并拓展四人的 PBL1/PBL2 中期报告，尤其需要更多可单独提交的设计图和组长内容。本轮以既有八份报告、模块分工及实际代码为基线，不增加无法由项目证据支持的个人实操结论。

## 2 决策过程

1. A 增加后端授权检查和故障恢复核对两张图，分别补足组长在权限边界与私域部署恢复方面的说明。图示表达设计及验收顺序，实际恢复测试仍需另行记录。
2. B/C/D 各增加一张针对个人模块的图：版本血缘、研究指标复算、页面请求身份。每张图嵌入该成员两份报告，并附文字解释，以便答辩时逐项说明。
3. B 的代码节选在新增图后落到单独末页，因此为代码行补充设计含义和可执行的验收观察，使该页成为完整的代码与证据说明。
4. 保留教师模板的封面、参考提纲和评分表；成员身份继续使用占位符。此次仅更新文档生成器、校验门禁和成品，无应用代码改动。

## 3 修改位置

| 内容 | 位置 |
| --- | --- |
| 五张新增设计图 | `tools/build_pbl_midterm_figures.py::permission_path`、`recovery_path`、`main`；`outputs/pbl-midterm-reports-2026-11-21/assets/` |
| 图嵌入和 B 代码说明 | `tools/build_pbl_midterm_reports.py::build_pbl1`、`build_pbl2`、`add_b_code_explanation` |
| 图片数量与文件门禁 | `tools/check_pbl_midterm_reports.py::FIGURE_ASSETS`、`main` |
| 八份报告 | `outputs/pbl-midterm-reports-2026-11-21/final/` |
| 图册、总索引、模板执行说明 | `docs/PBL_MIDTERM_FIGURE_CATALOG_2026-11-21.md`、`docs/PBL_MIDTERM_REPORTS_2026-11-21.md`、`outputs/pbl-midterm-reports-2026-11-21/artifact.md` |
| 四人责任材料 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 4 验证结果

- 生成脚本重新生成八份 DOCX 和十二张可独立提交的 PNG；结构检查通过，A 两份分别含 6/5 张内嵌图（含模板校徽），B/C/D 两份各含 4 张。
- 打包 LibreOffice 使用临时 PingFang 字体逐份渲染。A 两份均 20 页，B/C 各两份均 17 页，D 两份均 16 页。接触图检查所有页面，另放大核对 B 的末页代码说明，未见空白正文页、裁切或重叠。
- 原始教师模板保持只读，未知身份未虚构。设计图不得称作运行截图，文档生成与自动检查不代替队长最终人工产品验收。

## 5 未决事项

提交前填写四人的真实姓名、学号、班级和教师信息，使用最终 Word/WPS 环境快速复核分页；队长仍需按已建立的责任清单补实际页面操作与最终验收记录。
