# CHG-20261026-017 网页与新报告曲线纳入诊断已知日期

## 问题与决策

此前净值图仅用曲线自身日期并集，IC 图按 IC 序列位置绘制。即使 `daily_coverage` 已记录一个已知样本日，只要全部曲线在该日没有点，前后两个值仍会跨日连线。决定将可用逐日诊断日期也并入网页和新 HTML 报告三类图的横轴，并在该日断线；网页 IC 图显示显式空值与已知无记录日期的不同计数。旧结果无逐日诊断时仍按保存序列日期绘制。横轴仍是已知日期等距，并非自然日距离或独立交易所日历。不改收益公式、任务结果、CSV 或旧报告归档。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/chart-series.ts::alignNavLines`：接受可选已知日期，与线点日期形成排序并集；缺点拆分片段。
- `frontend/src/main.tsx::IcSeriesChart`、`NavChart`、`SavedSeriesCharts`：从当前 Run 的 `daily_coverage` 传入已知日期；IC 也按共同索引断线，起止日与文案更新，下载仍读取原始序列。
- `backend/app/services/reports.py::_align_dated_chart_series`、`build_report_html`：IC/Rank IC、多空、各组净值分别与已知诊断日期对齐后送既有 SVG 画图器；新报告横轴说明更新。
- `frontend/tests/chart-series.test.ts`、`backend/tests/test_reports.py`：构造两端有值、中央只有诊断日期的断线和报告实际 HTML 回归。
- `docs/SINGLE_FACTOR_ANALYSIS.md`、本索引及 A/B/C/D 四责任包：记录结果口径与实测边界。

## 验证与未决事项

后端 294 项、前端 81 项、前端构建和黄金样例通过；台账及文档链接检查见本轮提交。未启动容器或浏览器，本轮“诊断独有日期造成图形断点”由构造自动化验证，尚未在真实旧 Run 页面实点。若诊断和全部序列共同漏一市场日，仍不能识别该日；状态也不能独立归因停牌或缺行情。已有报告归档不回写，队长本人产品实测仍待完成。
