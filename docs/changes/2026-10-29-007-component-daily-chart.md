# CHG-20261029-007 任务中心成分逐日 IC 曲线

## 问题与决策

上一轮新 Run 已留存并可导出四成分逐日 IC，但研究员要判断时间变化仍需下载 CSV。决定在任务详情为具备逐日序列的 Run 增加可展开曲线，复用现有 IC/Rank IC 断线与日期核对组件；一次只显示一个成分，因子可切换，并在选中日期披露共同样本数。旧摘要 Run 不显示曲线入口。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 曲线标题与逐点样本数复用 | `frontend/src/main.tsx::IcSeriesChart` | 保持单因子与成分曲线相同的缺值和日期读数规则 |
| 可展开成分选择与任务详情接入 | `frontend/src/main.tsx::ComponentDailyIcPanel`、任务中心 `task-component-ic` 区 | 从当前 Run 已保存的逐日结果直接核对时间变化 |
| 面板及窄屏布局 | `frontend/src/layout.css::.component-daily-panel` | 控制选择器和图表宽度 |
| 口径、浏览器证据、总索引与四责任包 | `docs/MULTI_FACTOR_ANALYSIS.md`、`docs/HISTORICAL_COMPONENT_IC_CHART_QA_2026-10-29.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 记录决策、位置与验收 |

## 验证与未决事项

前端 89 项测试和生产构建通过。隔离浏览器实点新 Run 因子切换、年末/年初日期、原始 IC/Rank IC 及 299/300 条当日共同样本；旧摘要 Run 无曲线。375 px 页面无整页横向溢出，截图视觉检查通过，控制台 0 error/0 warning。隔离项目关闭后主 `fbl` 仍 `running(5)`。本轮未改后端或重跑后端测试；队长人工验收、Windows 和数据来源授权核验未进行。台账、链接和差异检查随提交执行；用户修改的分工 Excel 不处理。
