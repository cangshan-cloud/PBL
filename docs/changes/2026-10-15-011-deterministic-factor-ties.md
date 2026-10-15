# CHG-20261015-011：因子同值时固定分组次序

- 日期：2026-10-15
- 类型：research reproducibility + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

单因子检验按因子值排序后按名次分组。Python 稳定排序在因子值相同的时候保留输入顺序；若并列值跨过组边界，同一批证券只是换了 CSV 行顺序，就可能产生不同的分组收益、多空收益和换手率。课程验收要求相同输入集合可复现，因此决定只在因子同值时增加证券代码升序作为第二排序键。该规则是确定性的工程约定，不暗示同值证券存在经济意义上的先后；不扩大到更复杂的并列值整组分配方法。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 因子值、证券代码双键排序 | `backend/app/domain/research.py::evaluate` |
| 同值跨界且输入反序的分组、净值、多空结果回归 | `backend/tests/test_research.py::test_equal_factor_ties_have_input_order_independent_groups` |
| 明确同值排序约定 | `docs/SINGLE_FACTOR_ANALYSIS.md::指标定义` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_research -q`：12 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：151 项通过。
- `git diff --check`：通过。

## 风险与未决事项

新任务若存在跨组边界的并列因子值，数值可能不同于旧版本；已保存任务和报告不自动重算。证券代码只用于稳定打破并列，不作为额外因子。当前没有处理任意上游直接调用 `evaluate` 时的重复证券日期观测；正式 CSV 导入已拒绝重复证券日期。
