# CHG-20261015-025：每日证券数不足时跳过不完整分组

- 日期：2026-10-15
- 类型：research sample integrity + disclosure
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

普通任务只在所选证券总数层面检查 `symbols >= groups`，但因子窗口、缺行和标签过滤可使单日有效证券数低于目标分组数。原算法仍按名次给已有证券分配组号，部分组空缺，统计可能被误读为完整分组。决定按日判断：不足 `groups` 时保留可计算的 IC，不生成该日分组、净值及多空收益；只有 1 条观测的日期也计入跳过天数，但因无法计算 IC 不加入 IC 序列。该规则不拒绝整个任务，不把缺失组填零，且对旧 Run 不补推字段。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 每日分组最低样本检查与计数 | `backend/app/domain/research.py::evaluate` | 跳过不完整组，返回 `group_skipped_insufficient_sample_days` |
| 结论限制与 HTML 报告披露 | `backend/app/services/conclusions.py::build_run_conclusion`、`backend/app/services/reports.py::build_report_html` | 解释分组统计日期范围 |
| 工作台提示与兼容旧结果类型 | `frontend/src/main.tsx::Result`、研究结果区 | 只在正数时显示提示 |
| 混合日期、单条观测、结论与报告回归 | `backend/tests/test_research.py`、`backend/tests/test_conclusions.py`、`backend/tests/test_reports.py` | 防止缺组和计数回退 |
| 指标及结论口径 | `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/RESEARCH_CONCLUSION.md` | 固定解释边界 |
| 总索引 | `docs/CHANGE_INDEX.md` | 变更可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：168 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `npm run build --prefix frontend`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

旧任务及其报告不自动重算，和新任务可能不可直接比较。跳过日期不产生零收益或现金仓位假设，成本与换手依旧只按相邻可分组截面近似比较；项目仍非真实可成交回测。若未来引入更严格的最低组内样本数，应另作研究设计决策。
