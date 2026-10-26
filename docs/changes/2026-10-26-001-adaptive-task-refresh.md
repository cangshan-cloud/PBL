# CHG-20261026-001 任务列表自适应刷新

## 问题与决策

任务中心和实验对比页原来始终每 2 秒请求含完整结果的任务列表，即使所有任务早已结束。历史复现 JSON 单份约 326 KB，提示完整任务载荷可能较大，但它不是 API 响应大小实测。决定在待运行/运行任务存在时保持 2 秒，在全部结束、空列表或请求失败后改为 30 秒；每次请求结束后再调度下一次，避免定时器自身制造重叠。保留任务中心手动刷新，并为对比页增加手动刷新候选。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/task-refresh.ts::taskRefreshDelay`：按任务状态选择 2 秒/30 秒间隔。
- `frontend/src/auth-resource.ts::loadForLatestRequest`、`frontend/src/main.tsx::loadTasks`：较旧请求的响应与错误不覆盖较新请求，保存最近有效列表供调度判断；退出登录时清空快照。
- `frontend/src/main.tsx` 任务中心与实验对比 `useEffect`：由固定 `setInterval` 改为请求结束后 `setTimeout`；页面说明与手动刷新入口。
- `frontend/tests/task-refresh.test.ts`、`frontend/tests/auth-resource.test.ts`、`frontend/package.json`：状态分支、空/失败退避及同会话新旧请求竞态测试。
- `docs/TASK_REFRESH_BROWSER_QA_2026-10-26.md`、索引及 A/B/C/D 四责任包：记录隔离页面验收和未测边界。

## 验证结果与边界

前端 63 项测试与生产构建通过。隔离浏览器确认任务和对比页加载、手动刷新可用、控制台错误/警告 0；Playwright CLI 请求日志命令不可用，未宣称实测 2 秒/30 秒网络间隔或节省的字节数。后端全量回归、黄金核对、台账及链接检查见本轮提交。私有数据与用户修改的 Excel 未入库。
