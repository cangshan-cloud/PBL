# CHG-20261025-007 逐日诊断分页与历史页面验收

## 问题与决策

真实私有包浏览器任务成功后，研究工作台一次渲染全年 242 个逐日诊断行，页面及辅助技术导航过长。决定把显示层改为 20 日分页，保留全量任务结果和历史 CSV 导出，不调整研究计算或筛选口径。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/daily-coverage.ts::selectCoveragePage`：分页、边界收敛与空表处理。
- `frontend/src/DailyCoverageTable.tsx::DailyCoverageTable`：展示总日数、页码、上一页/下一页及当前日期行。
- `frontend/src/main.tsx` 研究工作台：用独立组件替换一次性全量渲染，并按 Run ID 重置页码。
- `frontend/src/styles.css`、`frontend/package.json`、`frontend/tests/daily-coverage.test.ts`：响应式操作区、测试入口及无重叠/边界回归。
- `docs/HISTORICAL_BROWSER_PAGE_QA_2026-10-25.md`、`docs/SINGLE_FACTOR_ANALYSIS.md`、PRD 矩阵、索引与 A/B/C/D 四责任包：记录真实页面证据和边界。

## 验证结果与未决事项

前端 53 项测试与正式构建通过。隔离 OrbStack 浏览器提交 Run `321b313b-218a-41c1-a433-638550751caa` 成功；242 日分为 13 页，首末日和前后页实点符合预期；报告在线预览与披露版 HTML 实际下载落盘，浏览器错误/警告均为 0。完整明细见 [浏览器记录](../HISTORICAL_BROWSER_PAGE_QA_2026-10-25.md)。后端全量回归、黄金核对、台账及链接检查见本轮提交。未做队长本人产品实测、Windows、移动端及独立行情/公式核验；用户修改的分工 Excel 未处理。
