# CHG-20261020-005 报告披露版交付副本

## 问题与决策

CHG-20261020-004 已在报告中心预览外提示旧合成报告，但原始 HTML 一旦下载并脱离平台，外层提示无法随文件传播。原归档文件受 SHA-256 校验，不能静默改写。决定保留既有 `/reports/{run_id}/download` 原字节接口，新增明确命名的 `/reports/{run_id}/delivery` 披露版副本；报告中心默认下载披露版。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/reports.py::report_delivery_copy`：对已校验归档的 HTML 生成副本，插入“非原始归档字节”标签、数据版本 ID/SHA、原报告 SHA。精确已知的 `demo_daily / 0.2.0` 合成版本提示休市行情；含周末行的版本提示人工复核；其他版本只说明不能据此认证真实交易日。插入值 HTML 转义，不写回归档。
- `backend/app/main.py::download_report_delivery_copy`：复用报告权限与原文件 SHA-256 校验；新增披露版附件接口，原始下载接口保持不变。
- `frontend/src/main.tsx::downloadReport`：报告中心按钮改为“下载披露版HTML”，文件名增加 `-disclosed`，说明原始归档保持不变。
- `backend/tests/test_reports.py`：测试合成与周末风险、来源转义、缺少页面结构拒绝、原下载字节和存储文件不变。

## 验证与限制

Mac 后端全量 231 项、前端 41 项和生产构建通过。确认 27 个任务均成功后定向替换 API、Worker、Web；数据库和 Redis 未重建。浏览器报告中心出现“下载披露版HTML”并实际点击。对同一旧演示 Run 的本机 HTTP 响应再次核对：原报告 SHA-256 为 `d70637a5839ecfe47b8764b959c980e7b9105130e3a89348a6d973125aeefe74`；披露版 38824 字节，含合成演示风险和“非原始归档字节”标记，响应头原 SHA 与原始下载实算一致。截图 `outputs/qa-2026-10-20/report-delivery-download.png`。核对后仍为 3 个数据版本、27 个任务、27 个报告产物。

披露版是派生交付文件，其 SHA 不等于原归档 SHA；文件内列出原 SHA 便于复核。若有人绕过报告中心直接调用原始下载接口，仍得到未追加披露的原归档，这是有意保留的证据接口。未独立核验浏览器保存到磁盘的文件字节；下载内容由同一新接口的 HTTP 核对覆盖。未做 Windows 测试。
