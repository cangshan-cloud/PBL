# CHG-20261020-010 公告休市风险报告链路端到端回归

## 问题与决策

CHG-20261020-009 已在单元层覆盖报告风险内容，但尚无从导入到报告交付的完整接口回归。主栈现有版本没有合适的新质量字段，直接导入测试样本会污染演示数据。决定用现有隔离 SQLite/TestClient 与临时目录，构造明确标为**合成**的小样本，完整走预览、绑定原文件 SHA 的导入、发布、研究任务、新报告和派生披露版下载。页面风险文案抽为纯函数，并单独验证报告 ID 与 SHA 双重匹配，避免引用错误数据版本。实际执行者：Codex。

## 修改内容与位置

- `backend/tests/test_api_journey.py`：新增 `test_calendar_risk_survives_import_run_and_report_delivery`；合成 2026-10-07 休市行及 2027 未覆盖年数据，核对质量字段、成功任务、报告索引数据身份、归档 SHA、披露版头与内容，并复读原归档确认字节不变。
- `frontend/src/dataset-alerts.ts`：新增 `reportCalendarRiskNotice`，统一报告外围提示中的行数、日期、未覆盖年和规则版本。
- `frontend/src/main.tsx`：报告中心使用经 ID 与 SHA 双重绑定的数据版本调用上述提示，删除原内联拼接。
- `frontend/tests/dataset-alerts.test.ts`：验证匹配版本显示完整文案、摘要不匹配或无质量异常不显示。
- `docs/ORBSTACK_DEPLOYMENT.md`、总索引与 A/B/C/D 四份独立验收材料记录本轮结果。

## 验证与边界

Mac 隔离目标测试 **1 passed**；后端全量 **238 passed**（另有一条第三方弃用警告）；前端 **43 passed** 且生产构建通过。`git diff --check` 通过。只重建并替换 Web 容器；API、Worker、DB、Redis 和数据卷未替换。五服务均运行，API/Worker/DB/Redis 健康；Web 容器内 `wget` 页面成功。更新后主栈仍为 3 个数据版本、27 个成功任务、27 份报告。Web 镜像 SHA-256 `b31e22570e74663051c1999e9b8f16479241f803edd290c62db4097d57ff2140`。

此处的“端到端”指隔离 HTTP API 流程，**不是浏览器实点**；本轮没有把合成 CSV 写入主栈。宿主沙箱 `curl 127.0.0.1:5173` 未连通，容器内部页面请求成功且 Web 日志显示监听，不能据此宣称宿主机浏览器可达。样本数值虚构，不构成真实市场或投资证据；Windows 仍未验收。
