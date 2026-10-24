# CHG-20261022-007 研究页防重复复权浏览器实点

## 问题与决策

CHG-006 的页面守卫只有逻辑测试和构建，还未证明研究员实际页面能从隔离库读取适配来源状态。决定复用专用数据卷做 Mac 浏览器实点。Web 容器构建停在 `npm install`，为避免长时间阻塞，改用本机 Vite 连接同一隔离 API；明确不把该结果称为容器化 Web 验收。实际执行者：Codex。

## 修改内容与位置

- `docs/MAC_PRICE_BASIS_BROWSER_QA_2026-10-22.md`：记录隔离配置、Web 构建边界、页面操作、禁用/恢复状态和收尾。
- `output/playwright/price-basis-guard-2026-10-22.png`：等权多因子错误复权口径页面截图；按钮状态另由 Playwright 可访问性快照核对。
- `docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、总索引及 A/B/C/D 四责任包：更新 Mac 页面证据和未完成的 Web 容器边界。本轮无代码改动。

## 验证与边界

隔离配置预检 PASS。研究员登录后，单因子与等权多因子选择 `factor_adjusted` 均出现错误提示且运行按钮禁用；改回 `source_close`，提示消失、按钮恢复。未点击提交，没有新任务。浏览器、Vite、隔离容器均已停止；`down` 未删除数据库卷或运行目录。截图与详细限制见 [验收记录](../MAC_PRICE_BASIS_BROWSER_QA_2026-10-22.md)。未完成 Web 容器构建、Windows 或队长本人验收。
