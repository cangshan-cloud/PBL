# 下游离线核对的严格 V2 口径（2026-10-28）

## 目的与用法

原有离线核对器会先验证复现包，但默认兼容 V1。现在历史审计 CSV、历史同源复算、每日序列 CSV 和保存结果内部审计命令均可追加 `--require-v2`；如缺少整包摘要的旧 V1 被误用于新版验收，会在读取其他输入前明确拒绝。省略选项时，旧归档仍按原口径兼容读取。

```bash
.venv/bin/python tools/verify_historical_audit_exports.py \
  data/real/historical_api_v2_20261028/reproducibility.json \
  data/real/historical_api_v2_20261028/daily.csv \
  data/real/historical_api_v2_20261028/unlabeled.csv \
  --report-html data/real/historical_api_v2_20261028/report.html --require-v2
.venv/bin/python tools/verify_historical_recomputation.py \
  data/real/historical_api_v2_20261028/reproducibility.json \
  data/real/bundles/hs300_2024_0375298bd2c8ac52/manifest.json --require-v2
.venv/bin/python tools/verify_research_result_consistency.py \
  data/real/historical_api_v2_20261028/reproducibility.json --require-v2
# 浏览器每日序列 CSV 如已下载，可对 tools/verify_series_exports.py 的命令追加 --require-v2。
```

## 实测与边界

使用前轮隔离 Celery 新 Run `dc520031-3a62-40d7-ac1e-1fa3e9d1456f` 的 Git 忽略四文件，严格历史审计核对为 4 因子、968 行逐日、32 条无标签信号且 HTML 摘要通过；严格同源复算为 4 因子、5 组、72,366 条有效观察；严格结果内部审计为覆盖/IC/分组各 242 日、有效观察 72,366。每日序列工具通过带构造 V2 整包摘要的测试正例；本轮没有为该新 Run 从浏览器下载序列 CSV，因此不宣称其真实文件已在严格模式验收。

反例测试用 V1 包对四个下游核对器均得到“not schema v2”，且在读取模拟缺失的 CSV/清单之前被拒。`run_isolated_historical_replay.py` 内部生成的新历史包也改为强制 V2 复算；`verify_historical_api_journey.py --require-v2` 将相同要求传给审计 CSV 核对。此选项只防意外版本降级，整包 SHA-256 无密钥，不能证明真实性、行情许可、公式独立正确或收益可成交。实际执行者：Codex；队长及其他组员未人工签收。

后续同日已在隔离真实浏览器对该新 Run 下载四份每日序列 CSV，并以严格 V2 模式逐行核对通过；本节此前“未下载”是当轮阶段事实，后续结果见[浏览器验收](V2_SERIES_BROWSER_QA_2026-10-28.md)。
