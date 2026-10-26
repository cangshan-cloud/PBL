# CHG-20261026-012 净值曲线按共同日期对齐并标注日期范围

## 问题与决策

原多空和各组净值图分别按数组下标绘线；日期集合不同时，同一横坐标可能指向不同日期，且曲线会跨缺日连线。决定用已保存点的日期并集做**结果日等距**横轴，单条曲线缺并集中的日期时断线；三张逐日图都标起止日期和非自然日口径。不引入独立市场日历，不更改收益或 CSV。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/chart-series.ts::alignNavLines`：构造排序日期并集、各曲线的连续片段和最后有效净值；缺日期或非有限值拆段。
- `frontend/src/main.tsx::NavChart`、`IcSeriesChart`、`SavedSeriesCharts`：净值点改携带日期、同轴画线并在缺日处断开；IC 和净值图显示起止日期及横轴限制，原图例与下载口径不变。
- `frontend/src/layout.css`：日期范围标签布局。
- `frontend/tests/chart-series.test.ts`、`frontend/package.json`：构造两组错位日期及非有限/空序列回归。
- `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/CHART_DATE_ALIGNMENT_QA_2026-10-26.md`、总索引及 A/B/C/D 四责任包：记录口径、浏览器实点与未测边界。

## 验证与限制

前端 80 项单测与构建通过；隔离旧 Run 浏览器显示三张图日期范围、非自然日说明，图例数值保持，控制台无错误。不同日期集的断线由构造测试验证，非此次真实旧 Run 浏览器实证。后端全量、黄金样例、台账和链接检查见本轮提交。图表仍不能证明数据来源、收益可成交或缺失市场日的原因；用户修改的 Excel 与私有证据不入库。
