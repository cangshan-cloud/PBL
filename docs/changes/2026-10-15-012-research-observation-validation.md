# CHG-20261015-012：单因子检验入口拒绝重复与非有限观测

- 日期：2026-10-15
- 类型：research input integrity + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

正式 CSV 导入已拒绝同一证券日期的重复价格行，多因子合成也拒绝重复因子观测；但直接进入单因子 `evaluate` 的观测没有同样的最后防线。重复观测会改变截面权重、排名及分组，非有限因子值或前向收益会污染统计结果。极端但有限的价格比值也可能在计算前向收益时溢出为无穷。决定在预处理之前逐条检查唯一性和有限性，违反时明确报错，不尝试删除、填补或猜测正确值。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 校验 `(trade_date, symbol)` 唯一及因子、前向收益有限 | `backend/app/domain/research.py::evaluate` |
| 重复观测、`NaN` 因子及无穷收益回归 | `backend/tests/test_research.py::test_evaluate_rejects_duplicate_and_nonfinite_observations` |
| 说明检验入口条件与失败行为 | `docs/SINGLE_FACTOR_ANALYSIS.md::时间对齐` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_research -q`：13 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：152 项通过。
- `git diff --check`：通过。

## 风险与未决事项

此前能传入但含重复或非有限观测的新任务现在会失败；已保存任务不重算。该保护不代替上游原始数据质量检查，也不处理有限但经济上异常的收益率；后者需要明确的数据清洗规则和验收样例后再决定。
