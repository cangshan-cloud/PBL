# 2026-10-16 当前版本 Web→API→Celery 浏览器隔离验收

状态：Mac OrbStack 五服务与真实浏览器技术流程通过；执行者为 Codex。不是十分钟连续讲解计时，也不是 Windows 实机验收。

## 环境和隔离

- 代码提交基线 `2f21021`；独立 Compose 项目 `factorlab-browser-qa-1016`，独立 PostgreSQL 卷／Redis，API 绑定 `127.0.0.1:18003`，Web 绑定 `127.0.0.1:5175`。
- API/Worker 只读挂载仓库 `data/sample`，共用临时报告目录 `/private/tmp/fbl-browser-qa-UijB67/runtime`；未挂载主栈 `data/runtime`，未使用主栈数据库。
- 合并配置已检查项目名、端口、API CORS、Web API 地址与卷映射；五服务启动，db/redis/api/worker 健康，宿主机 Web/API 均 HTTP 200。
- 浏览器快照、无密码只读页截图和两份下载文件保留于本机 Git 忽略目录 `output/playwright/compose-browser-qa-2026-10-16/`。该目录不是可分发的公开数据包。
- 验收后对精确项目名执行 `docker compose down`，仅移除本轮测试容器与网络；专用 PostgreSQL 卷和临时报告目录保留，主 `fbl` 服务未改动。

## 浏览器流程与结果

1. 研究员登录后见 1 个已发布数据版本、6 个因子、0 个任务；工作台默认 `demo_daily` 0.2.0、20 日动量、五组、单边 10 bps。
2. 页面点击“运行研究”后，Run `4c05d255-32b8-4e92-b89d-8647e3953448` 成功：1,980 有效观测、99 个有效 IC 截面、IC 均值 0.2451、Rank IC 0.2259、ICIR 1.4267，毛／成本后多空累计收益 58.83%／53.78%。这些是**合成演示数据**的软件输出，不是投资结论。
3. 任务中心显示固定的数据/因子/代码版本、参数、结构化结论和 `queued`、`started`、`dataset_loaded`、`factor_calculated`、`metrics_calculated`、`completed` 日志。独立 Worker 日志显示同一完整 Run ID 被 Celery 接收并成功完成，证明本任务不是 inline 模式执行。
4. 报告中心在线预览同一任务 HTML；浏览器分别下载 `factor-run-4c05d255.json` 与 `factor-report-4c05d255.html`。离线标准库工具返回 `result_verified=true`、`report_verified=true`。
5. 查看者登录后可见 1 个任务、1 份报告；概览“只读访问”和研究工作台“只读模式”按钮禁用。本轮验证了页面限制；后端拒绝写入由自动测试覆盖，未从该浏览器会话另发 403 请求。
6. Playwright 控制台检查：Errors 0、Warnings 0。记录的页面交互跨 03:13:02–03:15:17 UTC，包含工具往返，不能充作十分钟口头讲解的计时成绩。

## 四责任包本轮结果

| 责任包 | 本轮代执行证据 | 未覆盖 |
| --- | --- | --- |
| A 集成 | 当前版本五服务、独立卷、端口/CORS、Web→API→Redis→Worker 同一 Run 与报告摘要 | Windows、正式部署备份与多人负载 |
| B 数据 | 固定 `demo_daily` 0.2.0 在容器只读输入中成功；私有 10 股样本 SHA-256 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652` 回归通过 | 来源许可、真实全市场历史时点核验 |
| C 指标 | 本次 99 个有效 IC 日与页面/报告一致；黄金样例脚本、后端 185 项测试通过 | 独立真实市场全样本重算、样本外有效性 |
| D 产品 | 浏览器登录、任务提交、日志、预览、下载、只读页面和 0 错误/警告；前端构建通过 | 正式连续讲解计时、队长后续亲测数据 |

上述四包均由开发者代执行并注明边界，不表述为四名成员分别亲测。结果与决策记录见 [`changes/2026-10-16-013-current-compose-browser-journey.md`](changes/2026-10-16-013-current-compose-browser-journey.md)。
