# CHG-20261015-019：普通 CSV 因子标签与窗口不跨缺失市场日

- 日期：2026-10-15
- 类型：research time alignment + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

普通 CSV 的因子计算原先逐证券按“下一条记录”取前向收益；若该证券在市场交易日缺行，`t+1` 实际可能是隔日或更久。20/5 日滚动因子也可能把缺行前后的证券记录压缩成完整窗口。历史沪深 300 专用模式已有严格市场日历，普通模式不能继续默认为连续。决定从本次选定证券的日期并集推断市场日历，要求收益标签恰好来自下一市场日，并要求滚动窗口在该日历上连续；缺行直接跳过观测，不前填、插值或使用复牌后收益。若全部所选证券同日缺行，日期并集无法识别，该局限明确保留，不假称拥有交易所独立日历。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 推断选定截面市场日期位置，基础动量跳过缺口 | `backend/app/domain/research.py::calendar_positions`、`momentum_observations` |
| 六个内置因子对前向标签和适用滚动窗口检查连续性 | `backend/app/domain/factors.py::_momentum`、`_volatility`、`_rolling_field`、`_point_field` |
| 个别证券缺行、其他证券正常的回归案例 | `backend/tests/test_factors.py::test_missing_market_day_does_not_compress_window_or_forward_label`、`backend/tests/test_research.py::test_momentum_does_not_use_next_available_symbol_row_as_next_market_day` |
| 研究口径、样本限制与真实小样本复核 | `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/SAMPLE_SELECTION.md`、`docs/REAL_A_SHARE_SAMPLE.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_factors backend.tests.test_research -q`：20 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：158 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- 本机 Git 忽略、SHA-256 为 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652` 的 10 股 CSV 只读重算：动量 960/96、反转 1110/111、波动率 960/96、换手率 970/97、PE 1160/116（观察数/日期数），与既有记录一致；未创建任务。
- `git diff --check`：通过。

## 风险与未决事项

新任务在个别证券缺行的数据上可能少于旧任务观测数；旧结果和报告不可变。日期并集不是完整交易所日历，无法发现全部所选证券同时缺行或单证券独有缺行；数据来源与停牌状态仍需外部核验。本次没有更改数据导入质量门槛，也未对缺行生成显式审计明细；若课程要求，应先设计独立日历字段和证据。新提交的 CI、真实 API/Worker 与 Windows 部署需分别核对。
