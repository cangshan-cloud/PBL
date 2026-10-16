# CHG-20261016-001：多因子成分观测入口校验

- 日期：2026-10-16
- 类型：composite input integrity + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

单因子 `evaluate` 已在预处理前拒绝 NaN/无穷大，但多因子底层函数先做各成分截面预处理，之后才对齐与检查共同样本收益。若无效观测落在交集外，可能被掩盖；落在交集内则可能在统计函数中产生不稳定报错。决定在多因子入口对全部成分观测的因子值和收益做有限数检查，且早于预处理；不把无效值自动填零或静默丢弃。正式 CSV 上游仍保留自己的数据质量检查。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 全成分有限数检查 | `backend/app/domain/composite.py::combine_factor_observations` | 直接调用时稳定拒绝非法观测 |
| 交集外 NaN/无穷大回归 | `backend/tests/test_composite.py::CompositeFactorTests.test_nonfinite_component_observation_is_rejected_even_outside_intersection` | 防止对齐掩盖脏数据 |
| 合成口径说明 | `docs/MULTI_FACTOR_ANALYSIS.md::合成流程` | 明确不填零、不丢弃 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_composite -q`：7 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：173 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

已保存任务与报告不自动重算。新任务若上游产生非法观测会明确失败，需要修复来源数据或因子计算；此检查不解决极端但有限数值导致的统计量溢出，后者需单独定义数值边界和回归。GitHub Actions 在本轮开始时因公开 API 返回 403 未能核验昨晚两次提交的结果，不能记作已通过。
