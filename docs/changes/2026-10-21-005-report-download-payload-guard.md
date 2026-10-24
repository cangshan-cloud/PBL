# CHG-20261021-005 报告下载内容守卫

## 问题与决策

上一轮解决了下载按钮无反馈，但前端只检查 HTTP 状态：若服务端或中间层错误地以 200 返回空正文或 JSON，页面仍会保存为 `.html` 并提示已发起。决定在保存前检查 Blob 为非空 `text/html`，异常时沿用现有失败提示。此校验是客户端防误报，不替代后端归档摘要、结构与授权检查，也不验证浏览器实际落盘。实际执行者：Codex。

## 修改内容与位置

- `frontend/src/report-download.ts`：读取 Blob 后检查 HTML MIME 与非空，再调用浏览器保存函数。
- `frontend/tests/report-download.test.ts`：成功案例明确 HTML MIME；新增空 HTML、JSON 与无 MIME 的 200 响应反例，要求不调用保存函数；保留保存异常分支。
- `docs/CHANGE_INDEX.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/ORBSTACK_DEPLOYMENT.md` 与 A/B/C/D 四责任包：记录决策、测试及验收边界。

## 验证与边界

Mac 前端 46 项测试通过，生产构建通过。本次未改后端，未重跑后端测试。仅构建并替换 OrbStack Web 容器，镜像 SHA-256 `f65fcd673b4973117cf14b876610ef8a83accbac34e5f12f84bbb04b4b4fe355`；其余服务未替换，五服务运行，本机页面 HTTP HEAD 为 200。本轮未浏览器实点新的异常响应分支、未独立读取下载落盘文件，不能将单测和页面可达性称为完整 P3 验收。实际执行者：Codex。
