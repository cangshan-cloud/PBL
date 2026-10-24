# CHG-20261020-008 2026 日历预览浏览器验收与成交量提醒修正

## 问题与决策

CHG-20261020-007 已通过接口和纯函数测试，但尚未在浏览器选择文件实点。用临时两行合成 CSV 只做适配预览后，页面正确显示 `2026-10-07` 和 v2 规则；同时发现文件没有成交量列却出现“确认成交量单位”提醒。决定让提醒只在成交量字段实际被映射时出现，并将适配器版本从 1.3.0 升为 1.3.1；不更改标准化数据或质量判定。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/cn_csv_adapter.py`：成交量单位提醒以 `volume` 映射存在为条件；`adapter_version` 升为 `1.3.1`。
- `backend/tests/test_cn_csv_adapter.py`：含/不含成交量列两分支，2026 日历预览仍有休市警告且无无关提醒。
- `docs/CN_DATA_ADAPTER.md`、`docs/ORBSTACK_DEPLOYMENT.md`、总索引与 A/B/C/D 四责任包记录行为。
- 浏览器验收截图 `outputs/qa-2026-10-20/calendar-preview-browser-final.png`。临时输入仅为 `date,code,close` 表头与 2026-10-07、10-08 两行虚构数值，测试后已删除；未点击“导入并检查”或发布。

## 验证与边界

Mac 后端全量 235 项通过；前端沿用 CHG-20261020-007 的 42 项测试与构建，未改前端代码。更新前确认 27 个任务均成功，仅重建 API 和 Worker；Web、DB、Redis 保留。浏览器复点后：预览提醒命中 2026-10-07、规则为 `sse-szse-announced-closures-2024-2026-v2`，只有公告休市警告，不再出现成交量单位警告。主栈仍为 3 个数据版本、27 个任务和 27 个报告产物。API 镜像 SHA-256 `2f4a87ad209471aa8506a49c4e1d647a32a9aee45b96e94e8634a36b4bf44903`，Worker `b642c5211fcdcd3dc1791a92d0ff0fd5c5912337fc6e1f399edb7befde621c92`。

这只是合成数据的预览测试，不构成真实行情来源证明，也未做导入、发布或 Windows 验收。
