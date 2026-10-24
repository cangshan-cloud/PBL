# CHG-20261021-007 浏览器报告下载落盘字节验收

## 问题与决策

前次页面只提示已发起下载，API 核对也未覆盖浏览器保存的文件。决定在应用内浏览器监听下载事件，取得实际保存路径，再由只读命令将该文件与同次 API 披露版响应逐字节比较；不把页面提示当作成功证据。Playwright CLI 包装器再次无输出，停止后使用应用内浏览器。实际执行者：Codex。

## 修改内容与位置

- `tools/verify_live_report_delivery.py`：可选 `--browser-file`，在四文件和响应头核对后比较浏览器文件与 API 披露版响应；输出披露版 SHA 和明确的浏览器文件验证状态。
- `backend/tests/test_live_report_delivery.py`：新增浏览器文件相同/篡改反例。
- `docs/REPORT_DELIVERY_VERIFICATION.md`、`docs/MAC_BROWSER_ACCEPTANCE_2026-10-21.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`、总索引及 A/B/C/D 责任包：记录证据与剩余边界。
- 截图 `outputs/qa-2026-10-21/browser-download-landed.png`：报告中心对应下载反馈。截图仅证明页面状态，落盘字节证据来自浏览器下载事件路径和命令核对。

## 验证结果与边界

应用内浏览器在已有 BaoStock 组合报告 `170ef350-457b-4684-a2c8-7dab5f6275cf` 上触发下载并返回本机保存路径；只对该路径读取，未改写。离线四文件核对、HTTP 响应头摘要和浏览器文件逐字节核对均通过：`verified=true`、`http_checked=true`、`browser_file_verified=true`，原归档 24,387 字节、披露版 24,941 字节，披露版 SHA-256 `041543222d86cc8bb36e6e5eae3714e882b541310a2f0fed00052552c1c8be8d`。后端全量 **246 passed**，一条第三方弃用警告。本轮未改前端、未重跑前端测试，也未替换容器。

这完成一份**已有报告**的 Mac 浏览器下载落盘验收；不等于所有报告下载均正确，不证明连续新数据导入→研究→报告页面流程、行情真实性/许可、Windows 或队长本人产品实测。
