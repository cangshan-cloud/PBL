# CHG-20261027-008 复现结果内部一致性只读审计

## 问题与决策

既有四份 CSV 核对只证明导出值与同源复现结果相等；结果内部仍可能出现候选/有效计数、跳过状态、序列日期或收益成本不自洽。决定新增独立只读命令，从已验 SHA-256 的结果中重算可由保存字段推导的约束。该工具不接触生产任务、不对原始行情重算因子，避免将内部一致性夸大为来源真实性。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_research_result_consistency.py::verify_result_consistency`：检查每日与总体覆盖算术、IC/分组状态和日期对齐、逐日成本/净收益/毛净值/净净值递推；先复用结果 SHA-256 校验。
- `backend/tests/test_research_result_consistency.py::ResearchResultConsistencyTests`：已重算哈希的计数、比例、状态、日期及成本/净值篡改反例，另验原哈希篡改。
- `docs/SERIES_EXPORT_VERIFICATION.md::复现结果内部一致性审计`、[只读验收](../RESEARCH_RESULT_CONSISTENCY_QA_2026-10-27.md)、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：用法、证据边界和分工留痕。

## 验证与未决事项

5 项定向测试通过；留存的真实历史 Run 输出 242 诊断日、242 IC 日、242 有效分组日、72,366 有效观测。完整回归见本轮提交。该工具未核对 IC 数值或各组净值数值，也不认证来源、授权或可成交性；一致伪造数据仍可能通过。时间切分摘要不在本轮范围。
