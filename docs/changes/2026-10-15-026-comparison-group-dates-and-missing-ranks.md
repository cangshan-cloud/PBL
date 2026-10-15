# CHG-20261015-026：对比实际多空日期与缺失排名

- 日期：2026-10-15
- 类型：comparison correctness + UI
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

实验对比原先只检查 IC 日期集合。最近新增了全同值、逐日样本不足的分组跳过规则：两个任务可有相同 IC 日期，却在不同日期计算多空收益和换手，因此仅凭 IC 日期宣布“可直接比较”不足。决定从每个不可变结果的 `long_short_series` 读取实际多空分组日期，额外检查共同日期和日期集合一致性，并把数量显示在页面、CSV、HTML。仍不在交集上重算旧任务。另发现缺失指标会被排序为最后一名，决定排名只纳入有限数值，不把缺失当作低绩效。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 实际多空日期集合、共同日期与警告 | `backend/app/services/comparisons.py::compare_runs` | 分组口径不同时不再误报完全可比 |
| 缺失或非有限指标不参与排名 | `backend/app/services/comparisons.py::compare_runs`、`_rank_value` | 无结果不显示名次 |
| 日期数量导出 | `backend/app/services/comparisons.py::comparison_csv`、`comparison_html` | 离线报告保留审计证据 |
| 页面共同日期提示 | `frontend/src/main.tsx::Comparison`、实验对比区 | 研究人员可见多空日期差异 |
| 同 IC 不同多空日期、缺失排名回归 | `backend/tests/test_comparisons.py::ComparisonTests` | 防止判断回退 |
| 口径文档与总索引 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md` | 说明决策与解释边界 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：170 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `npm run build --prefix frontend`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

历史 Run 不重算，旧任务如果缺少 `long_short_series` 会显示没有共同多空分组日期并触发警告。共同日期计数只用于审计，指标仍是各任务原始全区间结果；若需严格同区间收益对比，应另设新实验或设计受控再计算功能。排名未做显著性检验，不可视为投资表现结论。
