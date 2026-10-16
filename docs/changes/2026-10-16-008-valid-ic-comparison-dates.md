# CHG-20261016-008：实验对比共同有效 IC 日期

- 日期：2026-10-16
- 类型：comparison evidence correctness + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

实验对比原先把 `ic_series` 中出现的日期都计入共同 IC 日期，即使该日 IC 为 `null`。全截面因子同值或收益截面无方差时，日期存在但没有相关系数证据；因此两个任务可被错误显示为同日具有有效 IC。决定只把 IC 为有限数值的日期纳入各任务 IC 日期集合、共同日期、日期范围和可比性警告；保留原始全区间指标，不在交集上重新计算。前端和导出文案明确“有效 IC”，避免把标签日期误当作证据日期。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 有效 IC 日期集合与警告 | `backend/app/services/comparisons.py::compare_runs` | 空值日不虚增共同证据 |
| 导出名称 | `backend/app/services/comparisons.py::comparison_csv`、`comparison_html` | 离线文件使用同一口径 |
| 相同日期但一侧 IC 为空的回归 | `backend/tests/test_comparisons.py::ComparisonTests.test_null_ic_date_is_not_counted_as_common_effective_ic` | 防止日期误计 |
| 页面提示与有效截面标签 | `frontend/src/main.tsx` 实验对比区 | 研究人员可见统计范围 |
| 文档和总索引 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md` | 固定解释边界 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：180 项通过。
- `npm run build --prefix frontend`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

新对比结果的 `ic_date_count` 和共同日期数可能小于旧界面曾显示的数字；底层 Run、IC 序列与旧报告不变。此检查仍只比较有效日期是否一致，不保证两任务每天使用相同证券截面；若需严格共同证券日再计算，应另设受控对比功能。Windows 浏览器与本提交 CI 尚待核验。
