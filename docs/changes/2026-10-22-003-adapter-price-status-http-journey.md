# CHG-20261022-003 适配来源价格状态接口闭环回归

## 问题与决策

上一轮只验证报告生成函数及交付副本函数，尚未证明适配来源的 `adjustflag` 经 API 预览、实际导入、发布和研究任务后仍能进入报告。决定在现有隔离 SQLite HTTP 测试中新增一条完整链路；使用合成价格与 PE 字段，目的仅是验证软件数据传递，不将其解释为真实市场或财务时点有效性。实际执行者：Codex。

## 修改内容与位置

- `backend/tests/test_api_journey.py::ApiJourneyTests.test_adapter_price_status_survives_import_run_and_report_delivery`：以 `adjustflag=2` CSV 调用适配预览和 SHA 绑定导入，发布后以 PE 建立 inline 任务；核对版本元数据、报告列表的数据 ID/SHA、原归档 SHA、HTML 来源状态、交付响应头及原归档不变。
- `docs/CHANGE_INDEX.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` 与 A/B/C/D 四责任包：记录本轮证据和限制。

## 验证与边界

定向 `test_api_journey.py` **18 tests OK**；后端全量 **255 tests OK**。测试使用进程内 SQLite、临时文件和 inline 执行，不接触主栈或私有行情；没有浏览器落盘、Celery/Compose 或 Windows 验收。PE 是合成字段，未验证财务数据实际披露日期或投资有效性。
