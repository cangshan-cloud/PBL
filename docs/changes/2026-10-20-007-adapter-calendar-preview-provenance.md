# CHG-20261020-007 适配预览的休市日期与规则溯源

## 问题与决策

2026 年公告休市规则已上线，但适配预览此前只给出命中日期数和行数；具体日期虽在最终质量报告中，却不能在导入前从结构化预览核对。决定让预览携带全部命中日期和规则版本，并在页面明确展示。仍允许人工核对后导入，不自动删行或拦截。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/cn_csv_adapter.py`：预览 `validation` 增加 `announced_weekday_closure_dates`，沿用质量检查的完整日期清单；原有规则版本和未覆盖年份字段保持。
- `frontend/src/dataset-alerts.ts::adapterCalendarDetails`：只在命中日期或未覆盖年份存在时构造导入前提示，注明规则版本及“不自动删行”。
- `frontend/src/main.tsx`：适配预览出现时显示导入前日历核对文案；文件切换导致预览失效时沿用现有清除逻辑。
- `backend/tests/test_cn_csv_adapter.py`、`frontend/tests/dataset-alerts.test.ts`：覆盖 2026-10-07 命中、10-08 非命中、v2 版本、2027 未覆盖与无风险不显示。
- `docs/CN_DATA_ADAPTER.md`、总索引和 A/B/C/D 责任包记录口径与执行者。

## 验证与限制

Mac 后端全量 234 项、前端 42 项与生产构建通过。确认 27 个任务均成功后，仅重建 API、Worker、Web；数据库、Redis 和数据卷保留。主栈临时合成 CSV 调用 `/datasets/adapt/preview`，只预览不入库，返回 `2026-10-07`、规则 `sse-szse-announced-closures-2024-2026-v2`、未覆盖年份为空。核对后仍为 3 个数据版本、27 个任务和 27 个报告。未对浏览器本地文件选择做实点，页面文案由前端单测与构建覆盖；Windows 未测。2026 规则仍不是完整开市认证。

部署镜像 SHA-256：API `abae8efec8cbb5aa7fd947d761d1d52783bc9dad74c22ce5412ada663d2a2a90`，Worker `de04d8368e4e404b764150ffa26b5fb2b5c7d87f16123eacdb3310f88b9b5cb2`，Web `59af3e548fa35ad3861ec6e77fd19b3fdc89abba713677fa5607347452f46dac`。
