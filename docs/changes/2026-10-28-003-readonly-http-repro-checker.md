# CHG-20261028-003 固化只读 HTTP V2 复现包验收

## 问题与决策

前轮隔离 HTTP 证据由临时命令得到，容易在响应头大小写、目标地址和 Run 身份对齐上出现人工检查误差。决定增加只读 CLI：限制显式 loopback 地址并拒绝跳转，密码仅取环境变量，下载仅放短时临时目录；对既有成功任务核对 V2 整包/结果/报告及任务元信息，按需增加结果内部审计。不触碰主栈或新增任务。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_http_reproducibility.py::validate_api_url`、`LocalApiClient`、`verify_http_run`、`main`：本机 URL 限制、无跳转下载、大小写无关附件头、严格 V2 摘要及任务绑定、可选结果审计。
- `backend/tests/test_http_reproducibility.py::HttpReproducibilityTests`：正例及外部 URL、V1 降级、错绑、报告变动和缺附件头反例。
- `docs/HTTP_REPRODUCIBILITY_TOOL_2026-10-28.md`、`docs/REPRODUCIBILITY_EXPORT_CHECK.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：使用方法、真实隔离输出与边界。

## 验证与未决事项

五项定向测试及后端全量 314 项通过，黄金研究样例通过；隔离 OrbStack API 对既有历史 Run 的新 CLI 实测通过，三个摘要与前轮人工验收一致，242 日和 72,366 条有效观察的内部审计通过。QA 容器已关闭且保留其独立卷，主 `fbl` 未修改。工具只做本机只读既有 Run 验收；不代替新任务 Celery/浏览器、独立公式或行情授权检查。
