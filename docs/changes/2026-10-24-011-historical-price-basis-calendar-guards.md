# CHG-20261024-011 历史包复权标记与日历标记加载防线

## 问题与决策

封存包清单声明 `price_adjustflag=1`，报告也按这一后复权源价格解释，但历史研究加载原先未逐行检查行情 `adjustflag`；交易日历只选值为 `1` 的行，其他未知标记会被当作非交易日忽略，且非交易日重复/乱序可能未被发现。决定在研究加载时逐行要求 `adjustflag=1`，并对日历全行限定 `0/1` 与严格递增日期，异常包明确拒绝计算。保留现有因子、标签和空值口径。实际执行者：Codex。

## 修改内容与位置

- `backend/app/domain/historical_research.py::_bar`：拒绝与清单价格口径不符的逐行复权标记。
- `backend/app/domain/historical_research.py::_trading_days`、`load_historical_bundle`：校验全部日历标记及顺序，不静默跳过未知/重复/乱序行。
- `backend/tests/test_historical_research.py::test_historical_bar_rejects_wrong_adjustment_flag`、`test_historical_calendar_rejects_unknown_or_duplicate_flags`：覆盖合法正例与多类异常反例。
- `docs/HS300_BUNDLE.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：记载价格口径与日历边界。

## 验证与边界

历史研究定向 11 项、项目虚拟环境后端全量 271 项、黄金手算核对及变更台账 206 条索引/44 条近期 A/B/C/D 链接均通过。本机私有包只读加载成功（292 个含预热/次年标签的交易日、72,600 成员行、95,776 价格行）。远端 CI 结果待提交后核对。本改动不独立认证 BaoStock 历史价格、官方交易日历或数据授权，也不修改网页、数据库和封存原始文件。分工 Excel 保持原样。
