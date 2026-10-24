# CHG-20261022-005 已复权来源的提交前防重复复权

## 问题与决策

此前执行阶段会拒绝已标记前/后复权的适配版本再次选择 `close × adj_factor`，但单因子或多因子任务已被创建并进入排队后才失败。决定在提交前复用同一数据口径守卫，返回 HTTP 400 且不创建任务；执行阶段仍复核，以保护旧队列或异常路径。没有适配状态的普通 CSV 不据此推断真实复权口径。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/runs.py::_validate_dataset_price_basis`：只在请求 `factor_adjusted` 时检查适配来源状态；仅明确 `3`（不复权）或空状态不触发来源拒绝，已复权/畸形状态拒绝。
- `backend/app/services/runs.py::create_research_run`、`create_composite_run`：提交前调用守卫；`execute_research_run`：保留执行阶段复核。
- `backend/tests/test_api_journey.py::ApiJourneyTests.test_adapter_price_status_survives_import_run_and_report_delivery`：同一已发布适配版本的单因子、多因子二次调整均返回 400，任务列表不增长；默认 `source_close` 仍成功。
- `backend/tests/test_price_basis.py::PriceBasisTests.test_adapter_adjustment_provenance_blocks_double_adjustment`：验证已复权拒绝、明确未复权允许及畸形元数据保守拒绝。
- `docs/PRICE_BASIS.md`、`docs/CN_DATA_ADAPTER.md`、总索引与 A/B/C/D 四责任包：更新用户口径和验收边界。

## 验证与边界

定向价格口径 **4 tests OK**、HTTP 链路 **18 tests OK**；后端全量 **256 tests OK**。本轮未修改 `adj_factor` 数值算法，也不验证来源复权声明真实性；未更新运行中的容器，Mac OrbStack 前一轮实测不覆盖本次提交前守卫，Windows 未验证。
