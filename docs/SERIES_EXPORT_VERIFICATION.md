# 每日序列 CSV 离线核对

从同一个已成功 Run 下载 `reproducibility.json`、每日 IC、多空逐日、各组逐日净值及逐日样本诊断 CSV 中的所需文件。在项目根目录运行：

```bash
.venv/bin/python tools/verify_series_exports.py /路径/reproducibility.json \
  --ic-csv /路径/ic-series-xxxxxxxx.csv \
  --long-short-csv /路径/long-short-xxxxxxxx.csv \
  --group-nav-csv /路径/group-nav-xxxxxxxx.csv \
  --daily-coverage-csv /路径/daily-coverage-xxxxxxxx.csv
```

四个 CSV 参数可任意选择，但至少要给一个。退出码 0 会输出各文件核对的行数。工具先检查复现 JSON 的结构版本、重复键和结果 SHA-256，再按原日期与组别顺序逐行核对列名、完整 Run ID、空值与每个原始数值；多空 CSV 同时核对单边成本参数。逐日诊断还核对候选/有效/排除数、原始覆盖率与 IC/分组状态码；旧结果没有 `daily_coverage` 时不能核对该文件，不会臆造空序列。错 Run、缺行、换序、列被改动、非有限数值或结果校验和不符均返回非零。无有效分组日允许只有表头；各组 CSV 按组别展开 `run_id,group,date,nav`，这里的净值为未扣成本的毛净值。

这是一致性核对，**不是数字签名，也不是独立重算**。复现 JSON 的 `task.id` 未包含在 `result_sha256` 内；协调修改 JSON 身份与 CSV 身份仍可骗过本工具。应从可信平台分别取得文件，并核对任务页面身份。工具不认证行情来源、数据授权、因子公式、显著性或可成交收益。浏览器下载文件与复现包的真实历史 Run 核对见 [IC/多空记录](SERIES_EXPORT_QA_2026-10-26.md)、[各组净值记录](GROUP_NAV_CSV_BROWSER_QA_2026-10-26.md)及[逐日诊断离线记录](DAILY_COVERAGE_EXPORT_OFFLINE_QA_2026-10-27.md)，决策见 [CHG-20261026-009](changes/2026-10-26-009-series-export-verifier.md)、[CHG-20261026-010](changes/2026-10-26-010-group-nav-csv.md)和 [CHG-20261027-007](changes/2026-10-27-007-daily-coverage-offline-verification.md)。

## 复现结果内部一致性审计

可再对同一复现 JSON 运行只读检查：

```bash
.venv/bin/python tools/verify_research_result_consistency.py /路径/reproducibility.json
```

退出码 0 输出诊断日、IC 日、有效分组日和有效观测数。工具重算每日候选＝有效＋排除、覆盖率及总量，核对零观测/跳过状态与逐日 IC/多空/各组净值的日期集合，并按保存的双边换手和成本参数重算每日成本、净收益及连续毛/净净值。它能发现**即使有人重新计算结果 SHA-256**后的部分内部矛盾，但不验证每个因子值、IC 数值本身、各组净值数值、交易可行性或行情来源；一致伪造的结果仍可通过。真实历史留存包的审计及边界见 [只读验收记录](RESEARCH_RESULT_CONSISTENCY_QA_2026-10-27.md)和 [CHG-20261027-008](changes/2026-10-27-008-research-result-consistency-audit.md)。
