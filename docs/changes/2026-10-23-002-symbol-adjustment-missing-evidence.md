# CHG-20261023-002 逐证券复权乘数缺失证据

## 问题与决策

CHG-001 只用全版本 `missing_counts.adj_factor` 拦截全样本任务；指定证券时无法从总数判断缺值是否落在所选样本。决定让**新导入**版本的质量报告记录 `missing_adj_factor_by_symbol`，只保存有空值的证券与行数。提交前对用户实际选择的证券精确检查；旧版本没有该字段时不臆测、不回填，继续由执行阶段逐行校验。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/datasets.py::validate_csv`：在有效 CSV 行上汇总每只证券的空 `adj_factor` 行数，写入版本质量报告。
- `backend/app/services/runs.py::_validate_dataset_price_basis`：指定证券且新质量报告表明该证券有空乘数时拒绝创建单因子/多因子任务；无逐证券明细的旧版本保持原执行期校验。
- `frontend/src/research-config.ts::validateResearchConfiguration`、`frontend/src/main.tsx`：已选版本有逐证券明细时，所选证券包含受影响者即提示并禁用运行。
- `backend/tests/test_datasets.py`、`backend/tests/test_price_basis.py`、`backend/tests/test_api_journey.py`、`frontend/tests/research-config.test.ts`：覆盖归属计数、受影响子集拒绝、有效子集成功及旧元数据回退。
- `docs/PRICE_BASIS.md`、`docs/DATASET_FORMAT.md`、计划、PRD 矩阵、总索引及 A/B/C/D 四责任包：同步口径和验收边界。

## 验证与边界

后端全量 **261 项**、前端 **50 项**及生产构建通过。隔离 SQLite/TestClient 中，3 股 4 日样本只有第二只股票一行乘数为空：质量报告逐证券计数为 1；全样本及含第二只股票的请求提交前 400，选择另两只股票的 PE 单因子任务成功。未更新容器或实点浏览器。

该字段只标记空值，不认证乘数来源定义；非有限或非正数在导入时被拒绝，Worker 仍保留逐行校验。旧版本不可由全版本计数推断受影响证券，故不强行迁移历史质量报告。
