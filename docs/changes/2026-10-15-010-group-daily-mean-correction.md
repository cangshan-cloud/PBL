# CHG-20261015-010：分组平均收益统一按逐日组合口径

- 日期：2026-10-15
- 类型：research correctness + golden regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

原实现的分组净值先计算每个交易日的组内等权收益，再逐日连乘；但摘要中的 `group_returns.mean_return` 把全部证券日收益直接合并求均值。若各日可用证券数不同，摘要会隐含按每日证券数加权，与净值曲线代表的逐日组合口径不一致。决定保持既有分组与净值算法，只把摘要改为“有成员交易日的组内等权收益，再对这些交易日等权平均”。不重写已经完成的任务或历史报告。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 从逐条证券收益累积改为逐日组收益累积 | `backend/app/domain/research.py::evaluate` |
| 不等截面规模的回归案例（10%、40% 两日应得 25%，非证券行混合平均 30%） | `backend/tests/test_research.py::test_group_mean_averages_daily_equal_weight_returns_not_all_stock_rows` |
| 独立黄金验算增加不等截面规模案例 | `tools/verify_golden_research.py::main` |
| 明确分组平均收益和换手率定义 | `docs/SINGLE_FACTOR_ANALYSIS.md` |
| 记录黄金验算案例 | `docs/GOLDEN_RESEARCH_VERIFICATION.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python tools/verify_golden_research.py`：通过，含不等截面规模手算案例。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：150 项通过。
- `git diff --check`：通过。

## 风险与未决事项

每日可用股票数变化的未来研究任务，摘要均值可能与旧版本不同；这是口径修正，旧任务结果保持不可变，若需比较应重新运行。黄金案例为合成数据，不代表真实市场绩效。前端、API 字段和数据库结构均未变更。
