# CHG-20261026-018 已知日期曲线与报告状态列浏览器验收

## 问题与决策

CHG-20261026-016、017 已用自动化证明报告可保留诊断独有日期、曲线可在已知缺日断线，但上一轮尚未浏览器检查新增状态列的窄屏可达性，也未复点新版曲线的旧任务页面。决定只做隔离环境和合成排版样例的只读页面验收；若无缺陷，不为增加改动量而修改生产代码。实际执行者：Codex；队长本人未签收。

## 修改内容与对应位置

- 新增 `docs/KNOWN_DATE_BROWSER_QA_2026-10-26.md`：记载环境、旧任务与合成报告观察、量化滚动数据及证据边界。
- 更新 `docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：将本轮代执行验收和未完成的本人产品实测分开登记。
- 本轮**无生产代码修改**。检查了 `frontend/src/main.tsx::SavedSeriesCharts`、`frontend/src/chart-series.ts::alignNavLines` 及 `backend/app/services/reports.py::_daily_series_detail`、`build_report_html` 的页面输出。临时 HTML 位于 `/private/tmp`，未纳入仓库；被忽略的 Playwright 截图不作为可移植证据。

## 验证与未决事项

隔离旧 Run 三图的日期、图例和控制台无回归；合成报告在 390px 视口可滚动至两状态列且保留全空已知日期。详细数据见[浏览器验收记录](../KNOWN_DATE_BROWSER_QA_2026-10-26.md)。旧 Run 本身没有诊断独有日期，不能把浏览器结果宣传为真实市场缺日断线实测；该分支由构造测试覆盖。报告仅合成排版，不是正式归档。队长本人产品实测仍待完成。
