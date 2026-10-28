# 历史四因子合成逐股独立抽样核对（2026-10-28）

实际执行者：Codex。工具只依赖 Python 标准库，从封存包的源日历、每日成分和逐股行情 CSV 重算四因子、次一市场日收益、每日 MAD 截尾与总体标准差 Z 分数，再等权合成；它不导入平台研究引擎。输入是私有 Run 的 `observations.jsonl.gz`，逐股键集合和数值均需匹配。封存包与产物未纳入 Git。

```bash
.venv/bin/python tools/verify_hs300_bundle.py data/real/bundles/hs300_2024_0375298bd2c8ac52
.venv/bin/python tools/verify_historical_composite_spotcheck.py \
  data/real/bundles/hs300_2024_0375298bd2c8ac52 \
  /private/tmp/factorlab-historical-qa-JYdB72/artifacts/dc520031-3a62-40d7-ac1e-1fa3e9d1456f/observations.jsonl.gz \
  2024-03-19 --artifact-sha256 c97c48daebfa1fb81867eaeff2e8632ffec2f5fb282f079cba3b12f403899778
```

| 信号日 | 成分数 | 同 Run 逐股核对 | 排除 | 最大合成值绝对差 | 最大次日收益绝对差 |
| --- | ---: | ---: | --- | ---: | ---: |
| 2024-01-02 | 300 | 300 | 无 | `4.44e-16` | 0 |
| 2024-03-19 | 300 | 299 | 下一市场日停牌 1 | `4.44e-16` | 0 |
| 2024-12-30 | 300 | 299 | 连续窗口缺交易行 1 | `8.88e-16` | 0 |

三个日期均使用新 Celery Run `dc520031-3a62-40d7-ac1e-1fa3e9d1456f` 的私有观测产物，产物 SHA-256 为 `c97c48daebfa1fb81867eaeff2e8632ffec2f5fb282f079cba3b12f403899778`。正例同时核对这些日期的**完整成分证券键集合**，因此不能通过只比较恰好存在的几只股票掩盖缺失。构造单测确认合成值篡改、缺少证券均失败。

本轮证据支持三个截面的源 CSV 到 Run 观测一致性，不是全年 72,366 条逐股独立重算，也不认证 BaoStock 来源授权、指数成分的官方生效、价格复权或投资收益可实现性。该产物路径属于隔离验收目录，换机器时应使用该机同一 Run 的私有观测文件及其已记录 SHA-256；不能用复现 JSON 代替逐股产物。队长和其他组员尚未人工签收。
