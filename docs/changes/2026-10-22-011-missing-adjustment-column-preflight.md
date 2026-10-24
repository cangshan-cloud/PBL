# CHG-20261022-011 缺少复权乘数列时提交前拒绝

## 问题与决策

原有 `factor_adjusted` 会在执行时逐行校验 `adj_factor`，但数据版本若根本没有该列，单因子或多因子任务仍可能先创建再失败。为避免可预见的失败任务，决定在提交前用已发布版本的质量报告列清单拒绝缺列；前端读取同一列清单给出即时提示。已复权来源状态的防重复调整守卫优先保留。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/runs.py::_validate_dataset_price_basis`：`factor_adjusted` 在来源状态校验后要求版本质量报告包含 `adj_factor`；单因子/多因子创建路径与执行路径共用。
- `frontend/src/research-config.ts::validateResearchConfiguration`、`frontend/src/main.tsx`：所选版本有列清单且缺 `adj_factor` 时，页面提示并禁用运行；服务端仍是最终防线。
- `backend/tests/test_price_basis.py`、`backend/tests/test_api_journey.py`、`frontend/tests/research-config.test.ts`：覆盖无适配标记、明确未复权标记、单因子/多因子 HTTP 400 与任务数不增加、页面提示及正常列放行。
- `docs/PRICE_BASIS.md`、计划、PRD 矩阵、总索引和 A/B/C/D 四责任包：更新决策与限制。

## 验证与边界

定向后端 6 项、后端全量 258 项、前端 48 项与生产构建通过。隔离 SQLite/TestClient 导入发布无 `adj_factor` 的 CSV 后，单因子与多因子 `factor_adjusted` 请求均返回 400，任务数不变。本轮未更新容器或实点浏览器；源数据中虽有该列但部分行缺失、非有限或非正数，仍由执行阶段逐行校验，不能仅凭列名认定复权乘数有效。`source_close` 不要求该列。
