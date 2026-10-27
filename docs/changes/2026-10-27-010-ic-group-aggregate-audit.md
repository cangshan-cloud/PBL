# CHG-20261027-010 全区间 IC 与分组收益内部交叉核对

## 问题与决策

现有只读审计能确认逐日计数和多空成本递推，却未检验展示在报告中的全区间 IC 摘要、各组平均收益以及多空毛收益是否与保存序列相互解释。决定只从保存的逐日 IC 与各组净值做算术复核，不重新读取原始行情；当某组净值已归零而无法从下一日净值反推日收益时，显式少计可核对日期，而不假定收益为零。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_research_result_consistency.py::verify_result_consistency`：复核 IC/Rank IC 均值、IC 标准差/ICIR/正比例；从各组净值反推组日收益，检查各组平均和多空毛收益；从多空逐日序列复核平均/累计毛净收益及平均双边换手，输出可核对组间收益日期数。
- `backend/tests/test_research_result_consistency.py::ResearchResultConsistencyTests`：已重算哈希的指标与组间错配反例，并覆盖零净值后收益无法反推和无有效 IC/分组日。
- `docs/SERIES_EXPORT_VERIFICATION.md::复现结果内部一致性审计`、[留存 Run 只读验收](../RESEARCH_RESULT_CONSISTENCY_QA_2026-10-27.md)、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：用法、结果和证据边界。

## 验证与未决事项

9 项定向测试通过；留存真实历史 Run 的 242 个分组日均可从组净值反推并与多空毛收益匹配，IC 摘要和其他聚合值也通过；完整回归见本轮提交。未独立计算逐股因子、IC 或组收益原始输入，也不验证行情来源或可成交性。一致伪造仍可通过。
