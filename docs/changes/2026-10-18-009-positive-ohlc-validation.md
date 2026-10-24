# CHG-20261018-009：导入时拒绝非正数开高低价

## 背景与决策

标准 CSV 已要求 `close > 0`，但可选的 `open`、`high`、`low` 只检验有限数和部分相对大小关系。`low=0` 或负值可能通过校验并进入已发布行情；这不是有效股票价格，也会使质量预览和后续研究建立在异常输入上。决定只对**实际提供**的开高低价增加 `>0` 约束，缺失可选字段仍允许，原有 OHLC 相互关系校验继续保留。`pe` 可反映负盈利，不应套用价格规则；成交量、金额、换手率、总市值维持非负约束，不扩大到上限或单位推断。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 开高低价正数校验 | `backend/app/services/datasets.py::validate_csv` |
| 标准 CSV 三字段异常及负 PE 边界测试 | `backend/tests/test_datasets.py::test_nonpositive_optional_ohlc_is_rejected_without_banning_negative_pe` |
| 中文适配器映射后复用校验测试 | `backend/tests/test_cn_csv_adapter.py::test_adapter_rejects_nonpositive_mapped_price` |
| 数据格式文档、总索引和四责任包 | `docs/DATASET_FORMAT.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 标准数据集定向 16 项、后端全量 212 项通过；私有 BaoStock 真实样本只读验证通过（原 SHA-256 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652`，1,170 行／10 股）。全量测试中的 CLI 安全拒绝提示来自预期保护用例，最终状态为 `OK`。
- 规则在管理员标准 CSV 上传和中文 CSV 适配后校验两条路径均生效；不静默修正价格，不改变已保存的数据版本。已有已发布版本不会自动重校验或迁移，历史数据质量仍需人工审计。
- 本轮不推断价格复权口径、涨跌停、停牌或 PE 披露时点；不构成投资结论。实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
