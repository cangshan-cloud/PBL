# V2 复现包隔离 HTTP 下载验收（2026-10-28）

## 范围与隔离

实际执行者：Codex；队长本人和其他组员尚未人工签收。OrbStack 恢复后，复用专用 Compose 项目 `factorlab-historical-qa-20261025` 的独立 PostgreSQL 卷与临时运行目录 `/private/tmp/factorlab-historical-qa-JYdB72`。运行 `tools/verify_historical_qa_compose.py` 预检通过，仅重建并启动该项目的 db、redis、api、web；API/Web 只发布至 `127.0.0.1:18022/15122`。未启动 Worker，未创建任务或更改既有任务。`docker compose ls` 同时显示主项目 `fbl` 的五服务仍运行；本轮未对其执行 Compose 命令。

## HTTP 操作与核验

以隔离研究员账号登录本机 QA API，读取旧成功 Run `f424f62b-4081-400c-89ef-79bbff4a4e59` 的任务响应，再经 HTTP GET 下载 `reproducibility.json` 与 HTML 报告。两份响应均有 `attachment` 文件名头；读取内容分别为 333,847 与 72,578 字节。下载文件仅写入自动清理的临时目录，用 `verify_reproducibility_export.py` 的 `require_v2=True` 路径核对；同一复现包再经 `verify_research_result_consistency.py` 审计。Run ID、成功状态及保存的 `result` 与任务响应相同。

结果：`schema_version=2`，`result_verified=true`、`bundle_verified=true`、`report_verified=true`；`result_sha256=61b3dafbf4ad0eb49e89c9bebfe74a3b335f9aa038d185a76e605c931472e1ec`，`bundle_sha256=c1c78be4fbdd70168adfe8ef9c41a6c3c4b613f6f0884347095992ac529abc24`，`report_sha256=0f15657d38f13dd5a2bb68ea4573eb2582847b38ba53d7702141280df6fbcdec`。结果内部审计：覆盖、IC、分组日期各 242 日，合格观察 72,366，组收益日期 242，直方图有效 IC 242。

第一次临时核验命令误用大小写敏感键读取 HTTP 响应头，错误地报告缺少 `Content-Disposition`；只读检查确认实际头名为小写 `content-disposition` 且两份均含附件信息。改为大小写无关判断后完整核验通过，服务端无需修复。

## 收尾与边界

验收后对**仅 QA 项目**执行 `docker compose down`，未使用 `-v`，保留独立数据库卷供后续检查；临时下载目录自动清理。此验收证明旧已保存 Run 可由新版隔离 API 动态导出 V2 并与报告/结果自洽，不等于主 `fbl` 服务已经重建为 V2，也不包含新建任务的 Celery 路径、浏览器点击、数据许可认证、独立公式验证或投资收益证明。
