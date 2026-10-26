# 每日序列 CSV 离线核对

从同一个已成功 Run 下载 `reproducibility.json`、每日 IC、多空逐日、各组逐日净值 CSV 中的所需文件。在项目根目录运行：

```bash
.venv/bin/python tools/verify_series_exports.py /路径/reproducibility.json \
  --ic-csv /路径/ic-series-xxxxxxxx.csv \
  --long-short-csv /路径/long-short-xxxxxxxx.csv \
  --group-nav-csv /路径/group-nav-xxxxxxxx.csv
```

三个 CSV 参数可任意选择，但至少要给一个。退出码 0 会输出各文件核对的行数。工具先检查复现 JSON 的结构版本、重复键和结果 SHA-256，再按原日期与组别顺序逐行核对列名、完整 Run ID、空值与每个原始数值；多空 CSV 同时核对单边成本参数。错 Run、缺行、换序、列被改动、非有限数值或结果校验和不符均返回非零。无有效分组日允许只有表头；各组 CSV 按组别展开 `run_id,group,date,nav`，这里的净值为未扣成本的毛净值。

这是一致性核对，**不是数字签名，也不是独立重算**。复现 JSON 的 `task.id` 未包含在 `result_sha256` 内；协调修改 JSON 身份与 CSV 身份仍可骗过本工具。应从可信平台分别取得文件，并核对任务页面身份。工具不认证行情来源、数据授权、因子公式、显著性或可成交收益。浏览器下载文件与复现包的真实历史 Run 核对见 [IC/多空记录](SERIES_EXPORT_QA_2026-10-26.md)及[各组净值记录](GROUP_NAV_CSV_BROWSER_QA_2026-10-26.md)，决策见 [CHG-20261026-009](changes/2026-10-26-009-series-export-verifier.md)和[CHG-20261026-010](changes/2026-10-26-010-group-nav-csv.md)。
