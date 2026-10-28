# 新历史 Run 每日 IC 独立验算（2026-10-28）

实际执行者：Codex。只读工具从该 Run 的私有 `observations.jsonl.gz` 逐股读取合成因子值和次日收益，用标准库单独计算 Pearson IC、平均并列名次 Rank IC，以及 IC 均值、总体标准差、ICIR、正 IC 比例；逐日与 V2 复现 JSON 中的保存结果核对。工具不导入项目研究算法。先使用已有 `verify_reproducibility_export.py --require-v2` 检查复现 JSON，再以已记录 SHA-256 固定观测产物。

```bash
.venv/bin/python tools/verify_independent_ic_from_observations.py \
  /private/tmp/factorlab-historical-qa-JYdB72/artifacts/dc520031-3a62-40d7-ac1e-1fa3e9d1456f/observations.jsonl.gz \
  data/real/historical_api_v2_20261028/reproducibility.json \
  --artifact-sha256 c97c48daebfa1fb81867eaeff2e8632ffec2f5fb282f079cba3b12f403899778
```

Run `dc520031-3a62-40d7-ac1e-1fa3e9d1456f` 的 **72,366 条逐股观测、242 个日期、242 个有效 IC 截面**均通过；每日 IC/Rank IC 和五项汇总的最大绝对差为 `1.11e-16`。固定六观测两日手算样本锁定 `0.5`、`-1` 两日 IC 及汇总 `-0.25`、`0.75`、`-1/3`；篡改每日 Rank IC、IC 均值、缺行、重复行、错误产物 SHA 均会失败。

这属于**从已有逐股观测到 IC 结果**的独立计算。它与此前三个日期的[源 CSV → 逐股观测独立抽样](HISTORICAL_COMPOSITE_INDEPENDENT_SPOTCHECK.md)形成局部证据链，但不等于全年原始 CSV → IC 的独立端到端复算，也不认证原始数据的授权、官方成分生效或未来收益。研究结果仍非可执行交易回测；队长和其他组员尚未人工签收。
