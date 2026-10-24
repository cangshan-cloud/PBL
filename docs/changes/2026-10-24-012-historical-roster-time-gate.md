# CHG-20261024-012 历史成员名单更新日期时点防线

## 问题与决策

历史研究加载逐日成员名单时原先只检查 `update_date` 非空，未验证日期合法性及其是否晚于查询日。自洽哈希的异常包可能将未来更新日期的成员放入当日股票池，形成显见的时点泄漏。决定在加载边界要求 `update_date <= query_date`，同时核对代码格式和原有 300 个不重复成员约束；不把这一防线误称为全部指数维护事件的官方生效认证。实际执行者：Codex。

## 修改内容与位置

- `backend/app/domain/historical_research.py::_roster_codes`、`load_historical_bundle`：解析更新日期、比较查询日，校验 `sh.`/`sz.` 六位代码、名单规模与重复代码。
- `backend/tests/test_historical_research.py::test_historical_roster_rejects_future_or_invalid_update_date`：覆盖正常 300 人名单、未来/空/非法日期及非法代码。
- `docs/HS300_BUNDLE.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：记录时点边界和运行时验收。

## 验证与边界

定向历史研究 12 项、项目虚拟环境后端全量 272 项、黄金手算校验及变更台账 207 条索引/45 条近期 A/B/C/D 链接均通过；本机私有包只读加载 242 个 2024 成员交易日、72,600 成员行、95,776 价格行。远端 CI 结果待提交后核对。此规则只识别明显未来/非法更新日期，不独立认证每次指数调样的实际生效日、ST 历史状态或数据授权。未修改网页、数据库或私有封存文件；分工 Excel 保持原样。
