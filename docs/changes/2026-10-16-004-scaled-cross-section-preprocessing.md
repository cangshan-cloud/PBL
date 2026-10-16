# CHG-20261016-004：截面预处理缩放计算

- 日期：2026-10-16
- 类型：preprocessing numerical stability + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

此前 `preprocess_observations` 直接对原始因子值计算 MAD、均值与标准差。`[-1e308, -1e308, 1e308, 1e308]` 均为有限数，但 `fmean` 在该截面会抛出 `OverflowError`；这些值不应被误判为 NaN，也不能静默填零。决定先按当日最大绝对值缩放，再执行既有 MAD 去极值与 Z-score。正比例缩放不改变因子排序或标准化结果；若关闭预处理或实际上无需变换，仍原样返回输入，避免浮点往返改变末位。`mad_scale` 同时限定为有限正数。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 截面缩放、MAD 与标准化、无操作保原值 | `backend/app/domain/research.py::preprocess_observations` | 极大有限值不再在预处理中溢出 |
| 大数及无操作回归、非法倍数回归 | `backend/tests/test_research.py::ResearchEngineTests.test_preprocessing_large_finite_cross_section_stays_finite` | 固定边界行为 |
| 预处理口径说明 | `docs/SINGLE_FACTOR_ANALYSIS.md::截面预处理` | 明确缩放不改变规则 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：176 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `.venv/bin/python tools/verify_real_a_share_sample.py`：五个真实 A 股因子的覆盖与分组日期数保持既有记录，全部通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

不同浮点计算路径可能使新任务的末位小数与旧任务不同；旧结果和报告不重算。极端值虽避免本次均值溢出，若因子跨度远超双精度分辨率，仍可能发生相近值合并；这属于数值精度限制，不应包装成有效信号。未经独立校验的异常行情仍应先检查数据来源与复权口径。
