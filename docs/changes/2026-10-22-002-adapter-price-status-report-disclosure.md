# CHG-20261022-002 适配来源复权状态进入报告披露

## 问题与决策

A 股 CSV 适配器已将 BaoStock 风格 `adjustflag` 保存在数据版本的 `quality_report.adapter_report.source_adjustment_flags`，并明确它不是 `adj_factor`。但新报告此前只写“导入的 close”，读者可能忽略来源已声明的前/后/不复权状态，甚至误把状态码当乘数。决定在单一有效状态存在时增加风险披露，并由动态交付副本复用；不推断实际复权算法、不修改旧归档或指标。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/reports.py::_dataset_risk_disclosures`：对适配来源 flag 1/2/3 分别写来源声明的后/前/不复权状态，说明只作元数据、任务默认用导入 `close`，要求核对原数据源。
- `backend/tests/test_reports.py::ReportTests.test_adapter_adjustment_status_is_disclosed_without_reapplying_factor`：新归档报告和交付副本均可见，1/2/3 三种状态均映射正确；空值或畸形嵌套值不伪造状态，也不使报告生成失败。
- `docs/CN_DATA_ADAPTER.md` 第 5 节、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` 的数据口径行：注明披露范围和剩余限制；总索引与四责任包同步。

## 验证与边界

报告定向 **14 tests OK**；后端全量 **254 tests OK**。只验证新生成 HTML 和动态交付副本的文本及口径，不重新计算任何价格、因子或收益，也不证明来源状态真实。本轮未部署容器或重做浏览器验收；旧归档字节保持不变，交付副本可根据当前绑定版本的元数据动态显示提示。
