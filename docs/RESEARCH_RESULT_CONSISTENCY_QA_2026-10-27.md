# 复现结果内部一致性只读验收（2026-10-27）

## 输入与结果

对 Git 忽略目录 `.playwright-cli/` 中此前浏览器下载的真实历史 Run `f424f62b-4081-400c-89ef-79bbff4a4e59` 复现 JSON 执行：

```bash
.venv/bin/python tools/verify_research_result_consistency.py .playwright-cli/reproducibility-f424f62b.json
```

输出 `{"daily_dates":242,"ic_dates":242,"group_dates":242,"eligible_observations":72366}`，退出码 0。没有重新下载、重跑研究或修改私有数据；原文件不入库。构造的 5 项定向测试覆盖已重算哈希后篡改计数/比例、状态/日期、成本/净值，以及未重算哈希。

## 证据边界

该结果只证明**保存结果内部**满足选定算术和日期约束；不是独立市场数据验算，也不能证明因子有效、可成交收益、历史股票池完整或数据授权。各组净值的数值与 IC 系列的数值未独立重算。留存 Run 不含 `time_split`，本轮不宣称真实分段摘要通过审计。开发者 Codex 执行，队长本人未签收。决策与位置见 [CHG-20261027-008](changes/2026-10-27-008-research-result-consistency-audit.md)。
