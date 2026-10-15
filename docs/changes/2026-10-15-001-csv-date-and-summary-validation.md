# CHG-20261015-001：CSV 日期格式与质量汇总有限性校验

- 日期：2026-10-15
- 类型：data quality fix + tests
- 状态：本机测试通过
- 关联提交：与本记录同次提交

## 背景与决策过程

数据格式文档要求交易日期为 `YYYY-MM-DD`，但 `date.fromisoformat` 也接受 `20250102` 等形式，导致接口实际约束比文档宽。另一个边界是单行浮点数都有限时，汇总 `sum(values) / count` 仍可能溢出为 `Infinity`，使质量报告出现非有限元数据。两者均属于导入时应明确拒绝的数据质量问题。本次选择严格校验标准 CSV 日期和汇总均值，不自动猜测或截断输入，以保证版本与质量报告口径一致。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 日期先匹配固定十字符格式，再交由日历解析；质量均值必须有限 | `backend/app/services/datasets.py::TRADE_DATE_PATTERN`、`_numeric_summary`、`validate_csv` |
| 紧凑日期、周日期、无效日历和有限输入汇总溢出的回归测试 | `backend/tests/test_datasets.py::DatasetValidationTests` |
| 明确格式与溢出处理口径 | `docs/DATASET_FORMAT.md::当前质量规则` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_datasets -q`：13 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：139 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：黄金指标独立验算通过。

## 风险、回退与未决事项

以前被宽松解析接受的紧凑日期或 ISO 周日期，现在需要在导入前明确转换为 `YYYY-MM-DD`；这不会改变已发布数据版本。极端正负值即使数学均值可有限，也可能因浮点中间求和溢出而被保守拒绝；A 股行情正常量级不受影响。该修复不增加 Parquet 导入、财务公告时点或行业数据链路。
