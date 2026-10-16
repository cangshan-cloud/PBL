# CHG-20261016-002：Pearson 缩放计算

- 日期：2026-10-16
- 类型：numerical correctness + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

原 Pearson 实现直接对中心化原值求平方和及乘积。对于 `1e200` 等有限数，平方和可能溢出为无穷大，随后得到 `inf / inf = NaN`；这会污染 IC 结果和 JSON 序列化。决定对两侧分别按最大绝对值缩放，再计算中心化点积与平方和；相关系数不随正比例缩放改变。输入包含非有限值时返回不可计算，零方差仍返回空值。未选择简单截断暴露值，因为会改变经济排序和相关结构。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 缩放、稳定求和及结果限定在 [-1,1] | `backend/app/domain/research.py::pearson` | 避免大有限数平方和溢出 |
| 大数正负完全相关及 `evaluate` 回归 | `backend/tests/test_research.py::ResearchEngineTests.test_pearson_large_finite_values_do_not_overflow` | 防止 NaN 回退 |
| 口径与边界 | `docs/SINGLE_FACTOR_ANALYSIS.md::当前假设与限制` | 区分相关计算与净值稳定性 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_research -q`：18 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：174 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

浮点计算细节可能使新 Run 的末位小数与旧版本不同，旧结果不自动重算。这里只修正 Pearson；极端但有限的前向收益仍可能使分组均值或净值连乘溢出，需要后续独立处理或明确输入边界。
