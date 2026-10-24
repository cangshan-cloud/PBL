# CHG-20261018-013：统一前端 Blob 下载与延迟释放

## 背景与决策

报告 HTML、任务复现 JSON、历史审计 CSV、实验对比 CSV/HTML 四类页面入口都在 `anchor.click()` 同步返回后立即调用 `URL.revokeObjectURL`。此前浏览器验收曾成功下载；上一轮另一次 CSV 点测仅到达 API 预检请求、没有 POST，不能证明立即释放是故障原因。不过立即释放存在浏览器尚未接管 Blob URL 的兼容性风险，也使四处清理逻辑重复。决定统一用临时挂载的下载链接触发，点击后移除节点，并在 30 秒后释放 Blob URL；保持请求、文件名和文件内容不变。30 秒只是兼容性缓冲，不是对下载完成时间的判断。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 统一下载助手、挂载／点击／移除／延迟释放 | `frontend/src/blob-download.ts::saveBlobAsFile` |
| 四类下载入口调用助手 | `frontend/src/main.tsx::downloadReport`、`downloadReproducibilityBundle`、`downloadHistoricalAudit`、`downloadComparison` |
| 顺序、延迟释放与点击失败清理测试 | `frontend/tests/blob-download.test.ts`、`frontend/package.json` |
| 导出说明、总索引和四人责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 前端 28 项测试、生产构建和 `git diff --check` 通过；新增单测确认节点先挂载再点击，点击后移除，URL 在延迟回调前未被释放；点击抛错时仍安排清理。
- 本轮没有浏览器再次下载或重跑后端测试；因此不宣称修复了上一轮仅 OPTIONS 的中断。若稳定环境再现，应检查页面重载、CORS/网络日志和请求会话状态。
- 延迟释放会让每次下载 Blob URL 最多保留约 30 秒，属于有限的短时内存成本；页面关闭时由浏览器回收。未改服务端文件、研究结果或权限。实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
