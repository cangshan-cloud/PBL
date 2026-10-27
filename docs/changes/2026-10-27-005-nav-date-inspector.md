# CHG-20261027-005 多空与分组净值增加逐日原值核对

## 问题与决策

IC/Rank IC 图已有按日期读数，多空与各组净值图仍需另下载 CSV 才能核对某日数值。决定让三类网页图共用日期读数组件：多空显示毛／成本后净值，各组显示各 Q 组净值；每张图独立选日，默认本 Run 末日，换 Run 重置。只读当前 Run 保存的图线数据，不重算收益，不把缺值补零。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/chart-series.ts::navInspectionRows`：按保存序列和可用逐日诊断日期合并排序，逐线保留高精度值或空值，并标出是否有任一原记录。
- `frontend/src/main.tsx::ChartDateInspector`：从原 IC 控件抽取共用日期选择、前后日按钮与逐线读数；控件以图名区分可访问名称。
- `frontend/src/main.tsx::NavChart`、`SavedSeriesCharts`：多空和分组净值接入共用控件，按 Run ID 独立重置；原 IC 控件也改用该组件，口径不变。
- `frontend/src/layout.css`：通用 `.chart-date-*` 样式，保持窄屏换行。
- `frontend/tests/chart-series.test.ts`：错位组日期、诊断独有日期、非有限值及原保存精度的构造测试。
- [隔离浏览器验收](../NAV_DATE_INSPECTOR_QA_2026-10-27.md)、`docs/SINGLE_FACTOR_ANALYSIS.md`、本索引与 A/B/C/D 四责任包：记录代码位置和验收边界。

## 验证与未决事项

前端 85 项测试和生产构建通过；隔离浏览器实点旧 Run 三图、日期独立切换、换 Run 重置及 390px 分组读数，控制台 0 错误/警告。真实旧 Run 没有用于实点缺值的样本，缺值行为由构造测试覆盖。后端、CSV、报告归档、私有原始数据、主服务及用户 Excel 未改；队长本人产品实测仍待完成。
