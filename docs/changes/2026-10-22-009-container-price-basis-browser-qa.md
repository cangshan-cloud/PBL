# CHG-20261022-009 容器化 Web 价格口径浏览器验收

## 问题与决策

CHG-008 仅证明 Web 容器可构建、入口 HTTP 200；CHG-007 的页面互动来自本机 Vite。决定在同一专用隔离 Compose 项目中用容器化 Web 实点研究员登录、单因子/等权多因子的复权口径拦截及恢复，不运行新任务。实际执行者：Codex。

## 修改内容与位置

- `docs/MAC_CONTAINER_PRICE_BASIS_BROWSER_QA_2026-10-22.md`：记录环境、交互、起止任务数、收尾和限制。
- `output/playwright/container-price-basis-guard-2026-10-22.png`：错误价格口径的容器化页面截图。
- `docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、总索引及 A/B/C/D 四责任包：更新验收证据和边界。本轮无代码改动。

## 验证与边界

隔离 Compose 预检 PASS。容器化页面成功登录研究员账号；合成适配版本 `adjustflag=2` 在单因子与等权多因子选择 `factor_adjusted` 时均显示具体警告并禁用运行按钮；改回 `source_close` 后警告消失、按钮恢复。起止总览均显示 1 条任务、1 份报告，没有点击运行。浏览器及隔离容器已关闭，`down` 未删除专用卷；主栈未动。未验证新任务、研究数值、真实行情状态、Windows 或队长本人操作。
