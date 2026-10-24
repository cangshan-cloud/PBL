# Mac 隔离栈新数据连续浏览器验收（2026-10-21）

## 环境与隔离

使用 `docker-compose.browser-qa.yml` 覆盖配置、项目名 `factorlab-browser-qa-1021`、专用数据库卷 `factorlab-browser-qa-1021_postgres_data` 和运行目录 `/private/tmp/factorlab-browser-qa-1021-moqdsy`。隔离 Web/API 仅绑定本机 `15121/18021`；API/Worker 只读挂载 `data/sample`，未挂载主栈 `data/runtime`。合并配置已逐项核对项目名、端口、CORS、卷；五服务启动且 API/Worker/DB/Redis 健康。隔离栈结束前计数为 2 个数据版本、1 个任务、1 份报告；主 `fbl` 栈只读计数仍为 3/27/27。

测试完成后仅对**精确项目名**执行 `docker compose ... down`，移除隔离容器及网络；未使用 `-v`，专用数据库卷及运行目录保留。主栈未停止或重建。Playwright CLI 包装器启动无输出而停止，改用应用内浏览器实点。实际执行者：Codex。

## 连续页面路径

1. 隔离库初始为内置演示版本 1 个、任务 0、报告 0。管理员浏览器登录，在数据页选择仓库 `data/sample/daily_prices.csv`；这是**合成演示 CSV**，不是独立真实行情。以 `isolated_browser_qa_20261021` 导入草稿：2,400 行、20 只证券、12 字段、SHA-256 `c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e`。质量报告提示 11 个公告休市工作日、220 行行情；发布为版本 `20261021.074752.526381`，版本 ID `b759c5a3-e6f0-4be5-ad93-0bb0970a2d43`。
2. 同一浏览器进入研究工作台，确认选择的是新发布版本，提交 20 日动量、20 日回看、5 组、MAD 3 倍、Z-score、单边 10 bps 任务。Run `e19a21cd-3259-43df-a260-ea182c31ec3e` 成功，页面显示 1,980 有效观测、IC 均值 0.2451、Rank IC 0.2259、成本后多空累计收益 53.78%。任务中心有排队、Worker 开始、`dataset_loaded`、`factor_calculated`、`metrics_calculated`、`completed` 日志。以上数值仅为合成数据软件结果。
3. 报告中心自动出现该 Run，预览 HTML 明确绑定新版本 ID/摘要并披露公告休市风险。浏览器下载 `factor-report-e19a21cd-disclosed.html` 后，`tools/verify_live_report_delivery.py --browser-file` 将实际落盘文件与隔离 API 披露版逐字节比较：`verified=true`、`http_checked=true`、`browser_file_verified=true`。原归档 38,510 字节、披露版 39,204 字节；原归档 SHA-256 `724e1bb59d596bdbf5321584ed2af7060f120c7a344f4f61a50621bda0873c8f`，披露版 SHA-256 `99bcd1bee23ae98a6c31f557c1f32dface65016dcbc2aa1524da112201f950c7`。

截图：`outputs/qa-2026-10-21/isolated-new-data-task.png` 与 `outputs/qa-2026-10-21/isolated-new-data-report.png`。截图只展示页面状态，文件一致性由浏览器下载事件路径与独立核对命令证明。

## 边界

这完成了 Mac 隔离栈中一次**新导入数据版本→异步研究→报告预览→浏览器下载落盘**的连续技术验收。所选 CSV 与内置演示数据同源、同 SHA，不能作为真实市场或独立数据有效性证据；这不是十分钟口头演示计时、队长本人产品实测、Windows 部署或证券数据许可证明。详见 [CHG-20261021-008](changes/2026-10-21-008-isolated-new-data-browser-journey.md)。
