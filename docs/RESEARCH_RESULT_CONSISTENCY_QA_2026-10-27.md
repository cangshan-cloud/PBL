# 复现结果内部一致性只读验收（2026-10-27）

## 输入与结果

对 Git 忽略目录 `.playwright-cli/` 中此前浏览器下载的真实历史 Run `f424f62b-4081-400c-89ef-79bbff4a4e59` 复现 JSON 执行：

```bash
.venv/bin/python tools/verify_research_result_consistency.py .playwright-cli/reproducibility-f424f62b.json
```

输出 `{"daily_dates":242,"ic_dates":242,"group_dates":242,"eligible_observations":72366}`，退出码 0。没有重新下载、重跑研究或修改私有数据；原文件不入库。构造的 5 项定向测试覆盖已重算哈希后篡改计数/比例、状态/日期、成本/净值，以及未重算哈希。

## 证据边界

该结果只证明**保存结果内部**满足选定算术和日期约束；不是独立市场数据验算，也不能证明因子有效、可成交收益、历史股票池完整或数据授权。各组净值的数值与 IC 系列的数值未独立重算。留存 Run 不含 `time_split`，本轮不宣称真实分段摘要通过审计。开发者 Codex 执行，队长本人未签收。决策与位置见 [CHG-20261027-008](changes/2026-10-27-008-research-result-consistency-audit.md)。

## 后续加强：IC 摘要和组间收益（同日）

在同一留存 Run 再运行命令，新增 `group_return_dates_checked: 242`；全区间 IC/Rank IC 摘要、各组平均日收益、多空毛收益与平均/累计净值摘要也与保存序列相符。9 项定向测试包含已重算结果哈希的聚合篡改、组净值与多空收益错配、净值为零后不可反推、无有效 IC/分组日。此后续并未重新计算原始股票收益；组净值与摘要是同源字段，仍不能证明市场真实性。见 [CHG-20261027-010](changes/2026-10-27-010-ic-group-aggregate-audit.md)。
