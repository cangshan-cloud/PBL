# CHG-20261023-007 复权缺失报告披露 HTTP 全链路回归

## 问题与决策

CHG-006 的测试只直接调用报告生成函数，尚未证明经 CSV 导入、发布、任务创建、自动归档和 HTTP 下载的完整链路均保留警告，且交付副本不改变归档。决定扩展既有逐证券缺失 HTTP 用例，复用同一隔离数据，不新增业务规则。实际执行者：Codex。

## 修改内容与位置

- `backend/tests/test_api_journey.py::test_missing_adjustment_values_reject_full_sample_but_not_valid_symbol_subset`：完整子集调整价成功后读取归档与披露版交付副本，核对全版本缺乘数文案、归档 SHA 头及不可变字节；再以 `source_close` 创建对照任务，确认不误报调整价警告。
- `docs/CHANGE_INDEX.md`、开发计划、PRD 验收矩阵和 A/B/C/D 四责任包：记录决策及验收边界。

## 验证与边界

单用例通过，后端全量 **262 项**通过；变更台账及 `git diff --check` 通过。测试使用隔离 SQLite/TestClient 与合成 CSV，未重新部署容器、未生成真实市场结论。已有归档字节不回写；本轮仅强化回归保护，未修改生产代码。
