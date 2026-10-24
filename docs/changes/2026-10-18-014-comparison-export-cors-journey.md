# CHG-20261018-014：对比导出跨域预检到 POST 的 HTTP 回归

## 背景与决策

上一轮隔离浏览器的一次 CSV 下载只在 API 日志中留下 OPTIONS 预检，没有对应 POST；当时页面重载，无法判断是服务端 CORS 拒绝还是浏览器会话中断。此前 HTTP 旅程测试只直接 POST，没有模拟浏览器跨域预检。决定在同一隔离 SQLite、已完成两条任务的旅程中，分别对 CSV/HTML 导出发送带 `Authorization` 与 `Content-Type` 请求头的 OPTIONS，再发送带 `Origin` 的认证 POST，并断言允许来源的 CORS 响应；另断言非白名单来源的预检被拒绝。不因单次浏览器超时改宽 CORS 白名单。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 两种导出 OPTIONS→POST 正向链路与非白名单来源拒绝 | `backend/tests/test_api_journey.py::test_comparison_api_and_exports_include_actual_group_dates` |
| 本轮诊断记录、总索引及四人责任包 | 本文件、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |
| 既有配置与中间件（本轮未修改） | `backend/app/config.py::parse_cors_origins`、`backend/app/main.py` 的 `CORSMiddleware` |

## 验证与边界

- 定向 HTTP 旅程 1 项、后端全量 212 项通过；`git diff --check` 通过。全量测试中 CLI 的“禁止非隔离写入”提示是预期保护用例，最终状态 `OK`。
- 允许来源 `http://127.0.0.1:5173` 的 CSV/HTML 预检返回 200、包含来源及 `authorization,content-type` 允许头，随后认证 POST 返回 200 和非空内容；`https://untrusted.example` 预检返回 400，不带允许来源头。
- 这是 ASGI `TestClient` 对 CORS/路由的回归，不是浏览器下载事件或自定义端口 15176 的完整端到端复现。它缩小了服务端故障可能性，但不能解释上一轮浏览器仅 OPTIONS 的确切原因；页面重载、浏览器网络策略或会话状态仍需在稳定环境复测。
- 不改变中间件配置、授权范围、导出内容或研究计算。实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
