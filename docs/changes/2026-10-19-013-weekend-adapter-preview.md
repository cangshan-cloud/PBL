# CHG-20261019-013 适配预览提前提示周末行情

## 问题与决策

上一轮把周末日期计数放入导入后的质量报告，但管理员用常见 A 股字段适配 CSV 时，预览阶段仍看不到该风险。决定复用标准 CSV 验证已经计算的计数，在适配预览报告中披露不同周末日期数、对应证券行数，并加入人工复核警告。仅诊断，不阻断导入、不删改行；原因是普通离线 CSV 没有权威交易所日历，不能据此判定所有交易日期是否合法。

## 修改位置

- `backend/app/services/cn_csv_adapter.py::adapt_cn_stock_csv`：适配报告版本升至 1.2.0，`validation` 增加两项周末计数，非零时增加导入前警告。
- `backend/tests/test_cn_csv_adapter.py::ChinaStockCsvAdapterTests.test_preview_warns_about_weekend_dates_without_dropping_rows`：验证计数、警告与不删行。
- `backend/tests/test_api_journey.py::ApiJourneyTests.test_weekend_diagnostic_matches_adapter_preview_and_import`：通过隔离 SQLite 与真实 HTTP 路由，验证同一 CSV 的预览、导入与质量报告一致。
- `frontend/src/main.tsx`：沿用已有适配预览 `report.warnings` 渲染和数据集质量提示，本轮未修改前端代码。
- `docs/CN_DATA_ADAPTER.md`、`docs/CHANGE_INDEX.md`、A/B/C/D 四责任包：补齐口径、位置、证据与边界。实际执行者：Codex。

## 验证与边界

适配器与数据集定向 28 项通过；新增隔离 API 旅程用例通过；后端全量 219 项通过。预览报告中同一周末两只证券计为 1 个日期、2 行，导入后的质量报告也是 1/2，原 3 行保留。前端未改代码，其通用警告列表可显示新增消息，但本轮没有完成浏览器文件上传实点，不能称为浏览器验收。

本轮尝试启动隔离 Vite/API 栈进行页面实点，服务进程启动后执行终端无法连接其本地端口，因此改用隔离测试客户端验证接口。该环境观察不是功能失败结论。尚未覆盖交易所节假日、临时休市、停牌或数据许可核查；旧数据版本不会自动回填新增计数。
