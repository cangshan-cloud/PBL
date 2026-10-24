# CHG-20261021-008 隔离栈新数据连续浏览器闭环

## 问题与决策

已有证据分别覆盖新文件导入和旧报告下载，但不能拼接为同一次新数据连续流程。决定使用独立 Compose 项目、数据库卷、运行目录和端口，避免主栈增加测试版本与任务；在同一浏览器会话完成合成 CSV 文件选择、导入、发布、异步研究、报告预览和实际下载文件核对。只用合成数据证明软件功能，不推断真实行情或投资结论。实际执行者：Codex。

## 修改内容与位置

- `docker-compose.browser-qa.yml`：隔离 Web/API 端口、CORS、API/Worker 运行目录与只读样本挂载；必须显式指定唯一 `-p` 项目名和 `FACTORLAB_QA_RUNTIME_DIR`。
- `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`：纠正过时验收状态，并区分 Mac 已验、PRD 偏差和最终未放行项。
- `docs/MAC_ISOLATED_BROWSER_JOURNEY_2026-10-21.md`：记录完整流程、版本/Run/摘要、隔离和限制。
- `docs/ORBSTACK_DEPLOYMENT.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`、总索引及 A/B/C/D 四责任包：同步技术验收和待办边界。
- `outputs/qa-2026-10-21/isolated-new-data-task.png`、`isolated-new-data-report.png`：任务日志与报告页面证据。

## 验证与边界

`docker compose config --format json` 核对专用项目 `factorlab-browser-qa-1021`、数据库卷、15121/18021 端口与临时运行目录，未指向主栈 `data/runtime`。五服务启动后隔离库从 1 个种入演示版本、0 任务/报告开始；新导入发布版本 `20261021.074752.526381`（2,400 行、20 股），Run `e19a21cd-3259-43df-a260-ea182c31ec3e` 成功且报告出现。浏览器保存的披露版与隔离 API 响应逐字节一致（39,204 字节、SHA-256 `99bcd1bee23ae98a6c31f557c1f32dface65016dcbc2aa1524da112201f950c7`）。隔离库结束前 2/1/1，主栈仍 3/27/27。隔离容器及网络已停止并移除；测试卷与运行目录保留，未使用 `down -v`。

此次未改产品算法或前端代码；合成文件与内置演示源相同，研究数值只用于软件验收。未完成队长本人产品实测、正式口头计时、真实行情许可和 Windows 验收。Playwright CLI 包装器在环境中未返回输出，页面实点改用应用内浏览器。
