# CHG-20261024-010 历史包研究加载校验 CSV 结构

## 问题与决策

历史包平台发布仅核验文件哈希；研究加载原先直接使用 `csv.DictReader`，没有检查表头与每行列数。自洽封存包中若出现额外列、缺失列、重复表头或某行列数不符，解析器可能静默忽略、产生 `None` 键或在下游抛出不明确的字段错误。决定在实际研究加载边界要求三类 CSV 的固定字段顺序和每行宽度一致；空字符串仍交给既有质量与可交易性规则处理。实际执行者：Codex。

## 修改内容与位置

- `backend/app/domain/historical_research.py::CALENDAR_FIELDS`、`ROSTER_FIELDS`、`PRICE_FIELDS`、`_verified_csv_rows`、`load_historical_bundle`：在同一已核验字节快照上校验三类表头和行宽。
- `backend/tests/test_historical_research.py::test_historical_csv_rejects_wrong_schema_and_row_width`：覆盖额外表头、行内多列及少列；既有字节快照测试同步传入预期表头。
- `docs/HS300_BUNDLE.md::历史包平台注册与发布`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：解释新增运行时防线和验收边界。

## 验证与边界

历史研究定向 9 项、项目虚拟环境后端全量 269 项、黄金手算核对与变更台账 205 条索引/43 条近期 A/B/C/D 链接均通过。本机私有包只读加载成功（72,600 成员行、328 证券、95,776 行价格）。远端 CI 结果待提交后核对。本改动不重新核对官方成分时点、来源授权或全部价格语义，也没有改动网页与已有封存文件。分工 Excel 保持原样。
