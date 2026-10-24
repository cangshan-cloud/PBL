# CHG-20261023-005 完整证券子集浏览器研究闭环

## 问题与决策

CHG-004 已从 API 提交证明 Worker 和报告可交付，却未证明研究员从 Web 点击“运行研究”到任务中心、报告中心及下载副本的连贯体验。本轮沿用隔离合成版本实点完整链路；只确认软件出口，不扩张为真实市场结论。实际执行者：Codex。

## 修改内容与位置

- `docs/MAC_SYMBOL_ADJ_GAP_BROWSER_RUN_2026-10-23.md`：记录配置、Run、页面状态、报告下载与边界。
- `output/playwright/container-symbol-adj-complete-run-2026-10-23.png`、`output/playwright/container-symbol-adj-complete-report-2026-10-23.png`、`output/playwright/container-symbol-adj-complete-report-2026-10-23.html`：保留研究页、报告页和下载副本证据。
- `docs/CHANGE_INDEX.md`、开发计划、PRD 验收矩阵及 A/B/C/D 四责任包：同步本轮决定与验收事实。
- 专用 QA PostgreSQL 卷：保留浏览器提交的 Run 与报告；无仓库业务代码修改。

## 验证与边界

浏览器实点后，Run `94cf90bd-f6a9-4bc5-8edd-dc14c191c969` 成功；任务中心参数与所选版本/证券/价格口径一致；报告中心归档同一 Run，披露版 HTML 下载 13,202 字节并含关键限制语。专用项目已 `down`，卷保留，主栈未动。

本轮未重测 API 400（前两轮已有记录）；2 股 4 日合成数据不能用于统计显著性或投资判断，Windows 和队长本人产品实测仍未完成。
