# 2026-10-16 开发者隔离彩排记录

状态：开发者技术彩排通过；**不是** D 成员的正式计时彩排，也不是四人个人签收。

后续约定更新：队长同日决定由开发者代执行并维护 A/B/C/D 四责任包，不再要求成员个人签收；本页末尾原“D/B/C 本人签收”要求保留为当时计划的历史文字，现以 [`TEAM_PLAN.md`](TEAM_PLAN.md) 新约定及 [`ASYNC_ACCEPTANCE_2026-10-16.md`](ASYNC_ACCEPTANCE_2026-10-16.md) 为准。正式连续计时仍未完成。

## 环境与范围

- 代码：`cd3a262` 工作树；Mac + OrbStack 主栈只做只读预检，未改其数据库或镜像。
- 主栈只读预检：宿主机 API/Web 均 HTTP 200；三个演示账号、`demo_daily` 0.2.0（2,400 行／20 只证券）、六因子、查看者列表、30 分钟活跃任务检查、备用报告 SHA-256 与 Worker ping 全通过。
- 浏览器彩排：临时 SQLite 数据库 `/private/tmp/fbl-rehearsal-B7a7Ln/rehearsal.db`、临时数据目录、当前代码 API `127.0.0.1:18001`（inline 模式）及 Vite `127.0.0.1:5174`。测试后停止临时服务；主栈原有 26 条任务未用作本次新任务。
- 浏览器下载和页面快照保留在本机 Git 忽略目录 `output/playwright/rehearsal-2026-10-16/`，不含账号密码；原始私有行情和临时数据库不纳入 Git。

## 实际步骤与结果

| 步骤 | 实际观察 | 结论 |
| --- | --- | --- |
| 管理员查看数据集和因子库 | 已发布 `demo_daily` 0.2.0，2,400 行、20 只证券、12 字段、0 缺失；六个因子及公式可见 | 通过 |
| 研究员按默认参数运行单因子 | 20 日动量、五组、单边 10 bps，Run `3b0d0a4c-c38c-410b-81bd-7d159047881d` 成功；1,980 有效观测、99 个有效 IC 截面 | 通过（隔离 inline 模式） |
| 任务中心 | 可见固定的数据／因子／代码版本、参数、结构化结论和 `queued` 至 `completed` 日志 | 通过 |
| 报告中心与下载 | 同一 Run 的 HTML 在线预览；浏览器下载复现 JSON 和 HTML；`verify_reproducibility_export.py` 返回 `result_verified=true`、`report_verified=true` | 通过 |
| 查看者角色 | 可见任务与报告数量；工作台“只读模式”按钮禁用，未创建新任务 | 页面权限通过；后端拒绝写入由自动测试覆盖，本次未单独发 403 请求 |
| 浏览器错误 | Playwright 控制台 `Errors: 0, Warnings: 0` | 通过 |

浏览器从 10:53:45 打开隔离页面到 10:56:48 保存只读截图，期间含自动化命令往返；这**不是** D 面向导师讲解的十分钟连续计时结果。未执行历史私有包展示、失败／取消分支、Windows 实机或当前提交的 Celery 新任务。主栈 Worker `pong` 不等于隔离 inline 任务经过队列。

## 可复核文件与自动测试

- 浏览器下载：`output/playwright/rehearsal-2026-10-16/factor-run-3b0d0a4c.json`、`factor-report-3b0d0a4c.html`（Git 忽略，本机文件）。可运行 `python3 tools/verify_reproducibility_export.py <json> --report-html <html>`。
- `git` 仓库内自动化：后端 182 项通过；`npm run build --prefix frontend` 通过；`tools/verify_golden_research.py` 通过。
- 私有 10 股 A 股样本回归：CSV SHA-256 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652`，1,170 行、10 股，五因子检查通过。该样本未随 Git 分发，也不是本次浏览器彩排数据。

## 正式放行仍需

1. D 本人用 [`FINAL_REHEARSAL_CHECKLIST.md`](FINAL_REHEARSAL_CHECKLIST.md) 连续计时、保存脱敏截图和失败记录，填写并签名。
2. A 核对正式演示提交的镜像／Worker 与 Git 版本一致；本次主栈镜像早于当前代码，不能据此宣称新提交 Celery 路径已验。
3. B/C 分别亲自核对数据来源与黄金指标，留计算过程、差异和署名；Windows 环境仍待实机验收。
