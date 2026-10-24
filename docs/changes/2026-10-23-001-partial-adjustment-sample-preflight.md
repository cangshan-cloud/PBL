# CHG-20261023-001 部分缺失复权乘数的全样本提交前校验

## 问题与决策

CHG-011 已拦截完全缺少 `adj_factor` 列的任务；但列存在而部分行空值时，全样本 `factor_adjusted` 任务仍会入队并在执行时失败。数据质量报告已有全版本 `missing_counts.adj_factor`，足以判断“不筛选证券”的任务必然失败，却不能确定空值属于哪些指定证券。决定只对未指定证券的全样本任务在提交前拒绝；指定证券时不以全版本缺失计数误拦截，仍由 Worker 在筛选后逐行检查。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/runs.py::_validate_dataset_price_basis`：增加可选证券样本参数；全样本且质量报告记录 `adj_factor` 缺失时拒绝创建，单因子/多因子及执行路径共用；有证券筛选时保留原逐行校验。
- `frontend/src/research-config.ts::validateResearchConfiguration`、`frontend/src/main.tsx`：读取所选版本缺失计数；未填写证券样本且选择调整价时即时提示并禁用运行。
- `backend/tests/test_price_basis.py`、`backend/tests/test_api_journey.py`、`frontend/tests/research-config.test.ts`：覆盖全样本拒绝、单/多因子任务数不变、有效证券子集可成功、导入价和零缺失放行。
- `docs/PRICE_BASIS.md`、计划、PRD 矩阵、总索引及 A/B/C/D 四责任包：同步口径和限制。

## 验证与边界

后端全量 **260 项**、前端 **49 项**及生产构建通过。隔离 SQLite/TestClient 导入含 1 个空乘数的 3 股、4 日 CSV 后，单因子/多因子全样本调整价均返回 400 且不建任务；选择没有缺失的两只股票，单因子调整价任务成功。前端测试首次失败是用例沿用了预填证券样本；改为真正的全样本输入后 49 项通过。

本轮未更新容器或实点浏览器。质量报告只给全版本聚合缺失数，不能用于推断指定证券是否完整；指定证券的缺失或无效乘数仍由执行阶段校验。列存在、缺失数为零，也不认证复权定义、真实行情许可或财务字段时点。
