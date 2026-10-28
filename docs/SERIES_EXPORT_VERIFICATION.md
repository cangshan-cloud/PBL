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

这是一致性核对，**不是数字签名，也不是独立重算**。旧 V1 复现 JSON 的 `task.id` 未包含在 `result_sha256` 内；新版 V2 增加整包摘要，正常修改身份或数据版本而不改摘要会被拒，但协调重写内容和摘要仍可骗过无密钥校验。新版验收可直接在上述命令末尾追加 `--require-v2`；省略时仍可读旧 V1。应从可信平台分别取得文件，并核对任务页面身份。工具不认证行情来源、数据授权、因子公式、显著性或可成交收益。浏览器下载文件与复现包的真实历史 Run 核对见 [IC/多空记录](SERIES_EXPORT_QA_2026-10-26.md)、[各组净值记录](GROUP_NAV_CSV_BROWSER_QA_2026-10-26.md)及[逐日诊断离线记录](DAILY_COVERAGE_EXPORT_OFFLINE_QA_2026-10-27.md)，严格模式边界见[新核对记录](STRICT_V2_DOWNSTREAM_QA_2026-10-28.md)。

## 复现结果内部一致性审计

可再对同一复现 JSON 运行只读检查：

```bash
.venv/bin/python tools/verify_research_result_consistency.py /路径/reproducibility.json --require-v2
```

对新 V2 文件建议保留 `--require-v2`；核对旧 V1 归档时省略即可。退出码 0 输出诊断日、IC 日、有效分组日、有效观测数，以及能从各组净值反推并核对多空收益的日期数。工具重算每日候选＝有效＋排除、覆盖率及总量，核对零观测/跳过状态与逐日 IC/多空/各组净值的日期集合；还从逐日 IC/Rank IC 核回全区间均值、标准差、ICIR、IC 为正比例，从有效 IC 核对十档固定区间直方图的边界、计数和总数（`histogram_ic_count`），从各组净值核回可完整反推时的各组平均日收益和多空毛收益，并从多空序列核回成本、换手、平均/累计毛净收益。若某组前一日净值已为零，下一日组收益无法仅从净值反推，该日不计入组间收益核对数，该组平均日收益亦跳过；零净值也不得无故恢复为非零。它能发现**即使有人重新计算结果 SHA-256**后的部分内部矛盾，但不验证每个因子值、IC 数值本身、原始组收益、交易可行性或行情来源；一致伪造的结果仍可通过。真实历史留存包的审计及边界见 [只读验收记录](RESEARCH_RESULT_CONSISTENCY_QA_2026-10-27.md)、[CHG-20261027-008](changes/2026-10-27-008-research-result-consistency-audit.md)、[CHG-20261027-010](changes/2026-10-27-010-ic-group-aggregate-audit.md)与 [CHG-20261027-011](changes/2026-10-27-011-ic-histogram-audit.md)。

若结果含 `time_split`，同一命令还会核对任务参数中的预设切分日、其前最后一个**有观测信号日**被隔离、研究期/验证期日期和观测数、有效 IC 日，以及从全区间逐日 IC/Rank IC 推导的两段均值、ICIR、IC 为正比例。输出额外包含两段信号日与有效 IC 日数；无切分结果保持原输出。它不重算 IC 本身，也不把回溯切分解释为前瞻检验。真实 10 股私有样本的两个临时切分 Run 验收见 [分段只读验收](REAL_SAMPLE_SPLIT_CONSISTENCY_QA_2026-10-27.md)与 [CHG-20261027-009](changes/2026-10-27-009-time-split-result-audit.md)。

2026-10-28 对隔离新 Celery Run 的四份**浏览器实际下载** CSV 已在 `--require-v2` 下逐行核对通过，见[浏览器严格 V2 验收](V2_SERIES_BROWSER_QA_2026-10-28.md)；这不替代独立市场数据或研究公式核验。
