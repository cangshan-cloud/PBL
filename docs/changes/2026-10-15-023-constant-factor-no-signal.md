# CHG-20261015-023：全同值因子截面不生成伪分组收益

- 日期：2026-10-15
- 类型：research correctness + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

此前每日所有证券的因子值完全相同，IC 与 Rank IC 为不可计算，但排序以证券代码打破并列后仍生成分组及多空收益。这会把代码字母顺序和偶然收益误呈现为因子效果。选择保留该日的 IC 空值与覆盖观测，跳过该日分组、净值和多空更新，并统计跳过天数；不拒绝整项任务，因为其余日期仍可能有有效信号。部分同值但至少存在两个因子值时，沿用证券代码稳定打破并列的既有规则。未选择以零收益填补，因为那会凭空制造日收益和净值点。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 全同值日期短路，返回跳过天数 | `backend/app/domain/research.py::evaluate` | 不再产生按证券代码排列的伪多空收益 |
| 报告披露跳过天数与口径 | `backend/app/services/reports.py::build_report_html`，分组结果节 | 研究人员能区分“无信号”和零收益 |
| 全同值、混合日期和部分并列回归 | `backend/tests/test_research.py::ResearchEngineTests` | 防止未来回退 |
| 指标定义与限制 | `docs/SINGLE_FACTOR_ANALYSIS.md` | 固定解释口径 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：164 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

旧 Run 的结构化结果及报告不自动改写，新任务可能与旧任务数字不同。跳过的日期不产生分组或多空净值点；成本和换手依旧只近似比较相邻可分组截面，并未模拟其间持仓、清仓或现金收益。若未来需要可交易回测，应单独定义无信号日持仓政策，而非在此版本暗中补值。
