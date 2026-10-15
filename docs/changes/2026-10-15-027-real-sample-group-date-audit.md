# CHG-20261015-027：真实样本分组日期审计

- 日期：2026-10-15
- 类型：real-data regression evidence
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

近期新增全截面因子同值与每日有效证券数不足时跳过分组的规则，以及实验对比的多空日期检查。既有真实 A 股验证脚本只输出覆盖量和 IC 日期，无法证明新规则没有意外删减分组日期。决定在原有私有 CSV 的隔离内存数据库复算中输出实际多空日期及两类跳过天数，并验证所有组净值日期一致且属于 IC 日历。脚本仍不修改现有平台任务或私有快照；真实样本未触发边界，不能替代合成边界回归。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 实际分组日与跳过计数审计 | `tools/verify_real_a_share_sample.py::group_date_audit`、`main` | 真实数据复测可发现日期错位 |
| 日期错位回归 | `backend/tests/test_real_sample_acquisition.py::RealSampleAcquisitionTests` | 防止脚本静默接受不一致结果 |
| 五个因子本机证据和解释边界 | `docs/REAL_A_SHARE_SAMPLE.md::使用与验证` | 明确真实样本未触发跳过分支 |
| 变更总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python tools/verify_real_a_share_sample.py`：通过；CSV SHA-256 为 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652`；五因子 IC/分组日期分别同为 96、111、96、97、116，两类跳过均为 0。
- `.venv/bin/python tools/verify_hs300_bundle.py data/real/bundles/hs300_2024_0375298bd2c8ac52`：独立封存完整性核验通过，576 文件、242 成分交易日；未执行历史研究任务。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：171 项通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

私有 CSV 和历史包不随 Git 分发，其他机器需另备数据。此验证只读原私有快照，并在临时目录与内存数据库中生成新任务；不证明旧持久化报告已重算，也不证明因子投资有效性。历史包本轮仅核验文件完整性，未做新的 API 端到端执行。
