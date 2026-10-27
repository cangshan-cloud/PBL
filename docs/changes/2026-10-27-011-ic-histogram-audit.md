# CHG-20261027-011 IC 十档分布内部核对

## 问题与决策

报告和页面展示保存的十档 IC 分布；既有离线审计已复核 IC 均值、标准差等摘要，却未检查分布档位和计数是否来自同一逐日 IC 序列。决定在只读审计中按研究规则重计 `[-1,1]` 固定十档，拒绝边界、行数或计数不符，空 IC 不计入。仍只核对保存结果内部，不独立重算市场数据或相关系数。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_research_result_consistency.py::_verify_ic_histogram`、`verify_result_consistency`：检查十档固定边界、字段、非负整数计数、IC 范围和各档计数，输出 `histogram_ic_count`。
- `backend/tests/test_research_result_consistency.py::ResearchResultConsistencyTests`：覆盖重新计算结果哈希后的计数/边界/缺档篡改、布尔计数及 `-1`/内部边界/`1` 分档。
- `docs/SERIES_EXPORT_VERIFICATION.md`、[留存 Run 验收](../RESEARCH_RESULT_CONSISTENCY_QA_2026-10-27.md)、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：说明检查和证据边界。

## 验证与未决事项

11 项定向测试通过；此前浏览器留存的真实历史 Run 中，有效 IC 242 个、十档分布总数 242，边界和各档均通过。完整回归见本轮提交。此检查不是独立因子/IC 重算或数据授权证明；保存的每日 IC 若整体错误而分布与之自洽，仍可通过。
