# CHG-20261016-005：旧结果对比的有限数边界

- 日期：2026-10-16
- 类型：legacy comparison resilience + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

新研究任务已在落库前拒绝非有限派生指标，但实验对比会读取历史 Run。若旧指标包含 NaN/Infinity，原对比直接携带这些值，JSON 序列化、差值或导出可能失败；`bool` 和异常大整数也可能被当作普通数值。决定仅在对比读取边界把这些值规范为缺失，不改写原始不可变 Run。缺失值不参与差值或排名，并在成本后收益缺失时提示。另修正 HTML 报告把全部“多空收益”笼统说成未计成本的文案，避免与成本后指标矛盾。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 读取旧指标时规范有限数、保护差值与排名 | `backend/app/services/comparisons.py::compare_runs`、`_finite_metric`、`_difference`、`_rank_value` | 非法数不进入对比 JSON、CSV、HTML |
| 成本后收益缺失提示与导出说明 | `backend/app/services/comparisons.py::compare_runs`、`comparison_html` | 不再把成本后收益说成未扣费 |
| 历史非有限指标和异常整数回归 | `backend/tests/test_comparisons.py::ComparisonTests.test_legacy_nonfinite_metrics_are_missing_in_all_exports` | 验证严格 JSON 序列化与导出 |
| 解释边界与总索引 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md` | 决策可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_comparisons -q`：8 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：177 项通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

对比视图中的空值仅代表该旧指标不可安全使用，不会修复旧 Run 或重新计算原始研究。旧任务中的其他字段（例如日期序列或参数）仍遵循已有格式假设；若出现结构性损坏，需要单独的产物审计与修复流程。当前未重新运行前端构建，因为前端代码未改。
