# CHG-20261027-006 IC 日期读数披露时间切分边界

## 问题与决策

设置预设时间切分的 Run 同时保存全区间 IC 序列与研究期／验证期摘要。边界前最后一个观测信号日会从两个分段摘要中隔离，但仍可能出现在全区间曲线；若网页只显示该日 IC 值，容易误认其参与验证。决定仅对带 `time_split` 的 IC 图展示已保存的分段日期与隔离日，并在日期读数区按两段实际保存范围标注阶段。日期在范围内不等于该日 IC 必然有效；不更改曲线、指标或验证资格。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/chart-series.ts::splitDateStage`：仅按保存的研究期起止、验证期起止和隔离信号日，将日期分类为研究期、隔离、验证期或范围外。
- `frontend/src/main.tsx::IcSeriesChart`：带切分结果时在全区间图下披露两段和隔离日期，说明隔离日点仍可能可见但不进入分段摘要。
- `frontend/src/main.tsx::ChartDateInspector`：在所选日期下显示阶段口径；无切分结果时不显示阶段提示。
- `frontend/src/layout.css`：阶段说明与窄屏文本样式。
- `frontend/tests/chart-series.test.ts`：覆盖范围端点、隔离日与范围外日期。
- [隔离浏览器验收](../IC_SPLIT_DATE_CONTEXT_QA_2026-10-27.md)、`docs/TIME_SPLIT_VALIDATION.md`、`docs/SINGLE_FACTOR_ANALYSIS.md`、本索引与 A/B/C/D 四责任包：记录取舍与证据边界。

## 验证与未决事项

前端 86 项测试及构建通过。隔离浏览器只在任务列表响应临时附加构造 `time_split`，实点三类阶段提示和 390px 排版，控制台 0 错误/警告；服务端原 Run 未被修改，构造的零计数不代表真实分段研究。后端计算、报告、CSV、私有数据和主服务不变。真实带切分 Run 的此 UI 路径及队长本人产品验收待完成。
