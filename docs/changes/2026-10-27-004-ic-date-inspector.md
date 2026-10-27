# CHG-20261027-004 每日相关性图增加按日期原值核对

## 问题与决策

IC/Rank IC 双线图在 242 日历史样本上较密，仅凭曲线与四位小数图例无法核对某日两项值。决定在图下增加原生日期选择与前/后一已知日期按钮，读取该 Run 已保存的 `ic_series`，以浏览器序列化数值展示，不插值、不补零、不重算。日期轴仍是结果日期与逐日诊断日期的并集；只有诊断日期而无保存记录时，明确提示“没有保存的相关性记录”。切换 Run 时选择重置到新 Run 的末日。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/chart-series.ts::icInspectionRows`：生成排序去重的已知日期列表，区分有记录但空值和仅诊断日期。
- `frontend/src/main.tsx::IcSeriesChart`：默认末日、前后按钮、原生下拉与两项未四舍五入的保存值；`SavedSeriesCharts` 按 Run ID 重新挂载该组件，避免旧 Run 选中日期串入新 Run。
- `frontend/src/layout.css`：核对区及窄屏换行样式。
- `frontend/tests/chart-series.test.ts`：构造高精度值、错位空值、诊断独有日期与空输入。
- [浏览器验收](../IC_DATE_INSPECTOR_QA_2026-10-27.md)、`docs/SINGLE_FACTOR_ANALYSIS.md`、本索引与 A/B/C/D 四责任包：记录决策、范围和执行边界。

## 验证与未决事项

前端 84 项测试、生产构建与隔离旧 Run 页面交互通过；390px 截图确认长数值换行，控制台 0 错误/警告。后端指标、CSV、报告归档、主服务及用户 Excel 未改。仅诊断日期且无保存相关性记录的页面提示有构造单测，尚无真实历史样本浏览器实点；队长本人产品验收仍待完成。
