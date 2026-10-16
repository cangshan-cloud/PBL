# CHG-20261016-003：派生研究结果有限数边界

- 日期：2026-10-16
- 类型：result integrity + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

[Pearson 缩放修正](2026-10-16-002-pearson-scaled-correlation.md)消除了相关系数平方和的一类溢出，但极端且有限的前向收益仍可能让多空差、净值连乘或 ICIR 变为无穷大。若继续保存，会在 JSON 序列化或复现包导出时失败，且错误位置不清楚。决定在 `evaluate` 返回前递归检查全部浮点派生指标，发现非有限值立即以路径化错误失败；多因子合成暴露值也在进入后续相关矩阵前做有限数检查。不为无穷大填零或截断，因为那会伪造研究结果。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 结构化结果递归有限数检查 | `backend/app/domain/research.py::_ensure_finite_result`、`evaluate` | 失败早于持久化，不保存 NaN/Infinity |
| 合成暴露值边界 | `backend/app/domain/composite.py::combine_factor_observations` | 不让异常暴露进入相关矩阵 |
| 极端收益导致派生多空溢出回归 | `backend/tests/test_research.py::ResearchEngineTests.test_nonfinite_derived_portfolio_result_is_rejected` | 防止非法 JSON 结果回退 |
| 口径和风险说明 | `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/MULTI_FACTOR_ANALYSIS.md` | 明确失败而非补值 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：175 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

极端输入的新任务可能从原先延迟序列化失败变为明确的计算失败；旧 Run 与报告保持不变。校验无法修复上游预处理自身抛出的溢出异常，也不为极端真实收益设定交易学意义上的截断阈值；若课程验收需要此类数据，应先核对源数据与复权口径。
