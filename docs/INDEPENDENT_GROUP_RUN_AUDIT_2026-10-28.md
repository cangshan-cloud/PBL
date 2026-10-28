# 新历史 Run 分组、多空与成本独立验算（2026-10-28）

实际执行者：Codex。标准库只读工具使用私有 `observations.jsonl.gz` 的证券日期、合成因子值和次日收益，按因子值及证券代码稳定排序，重建每日 5 组、各组等权收益和累计净值，再以相邻日期的顶部/底部目标持仓集合独立计算双边换手、固定 10 bps 成本、毛/净多空收益及净值。逐日和汇总均与 V2 复现 JSON 保存结果比较；不导入应用研究算法。

```bash
.venv/bin/python tools/verify_independent_groups_from_observations.py \
  /private/tmp/factorlab-historical-qa-JYdB72/artifacts/dc520031-3a62-40d7-ac1e-1fa3e9d1456f/observations.jsonl.gz \
  data/real/historical_api_v2_20261028/reproducibility.json \
  --artifact-sha256 c97c48daebfa1fb81867eaeff2e8632ffec2f5fb282f079cba3b12f403899778
```

Run `dc520031-3a62-40d7-ac1e-1fa3e9d1456f` 的 72,366 条观测、242 日、5 组、1,210 个组净值点和 242 条多空序列，以及组收益均值和六项多空/换手汇总全部核对通过，**最大绝对差为 0**。固定两日、4 股、2 组手算样本验证首日双边换手 2、次日顶部和底部完全互换后换手 4、成本分别为 0.002/0.004；篡改成本、组净值、净期末收益、缺少日期、错误成本模型及错误产物 SHA 均失败。

此工具只适用于当前固定 10 bps 成本、每天都有足够有效证券且因子非恒定的历史 Run；遇到不足样本或恒定因子日会明确失败，不把跳过的日子悄悄算作已验。应先分别核对 V2 复现包和观测产物 SHA。它补充了[源 CSV 到三日逐股观测](HISTORICAL_COMPOSITE_INDEPENDENT_SPOTCHECK.md)及[逐股观测到 IC](INDEPENDENT_IC_RUN_AUDIT_2026-10-28.md)的证据链，但不证明交易可执行、市场冲击、原始行情真实性或投资效果。队长和其他组员尚未人工签收。
