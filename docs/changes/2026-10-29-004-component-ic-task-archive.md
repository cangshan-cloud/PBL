# CHG-20261029-004 任务中心回看成分 IC 与旧 Run 缺字段提示

## 问题与决策

工作台的成分同样本 IC 只随当前提交后的任务显示。研究员在任务中心按 Run ID 回看已保存任务时看不到这一诊断，旧归档缺字段提示也无法通过现有回看入口验收。决定抽取同一展示组件，供工作台和任务详情共用；任务中心只读取原保存结果，不重算、不补零或修改旧报告。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 复用的成分 IC 表与缺字段文案 | `frontend/src/ComponentIcTable.tsx::ComponentIcTable` | 两处页面展示同口径，并明确旧 Run 无字段 |
| 工作台复用、任务详情回看入口 | `frontend/src/main.tsx::CompositeResult`、研究工作台合成诊断区、任务中心详情区 | 可按历史 Run 核对新旧结果 |
| 任务详情间距和窄屏表格约束 | `frontend/src/layout.css::.task-component-ic` | 保持内容可读，表格内滚动 |
| 口径、真实浏览器证据及四人责任包 | `docs/MULTI_FACTOR_ANALYSIS.md`、`docs/HISTORICAL_COMPONENT_IC_ARCHIVE_QA_2026-10-29.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 保留决策、代码位置和验收 |

## 验证与未决事项

前端 86 项测试和生产构建通过。隔离浏览器任务中心回看新 Run `9bbb1f11` 显示 72,366 条共同样本、四行 242/242 成分诊断；旧 Run `1af438dd` 显示未保存文案。375 px 整页不溢出，表格内部滚动；控制台 0 error/0 warning。隔离栈关闭后主 `fbl` 仍 `running(5)`。本轮未修改后端，未重跑后端测试；队长人工验收、Windows 与来源授权核验未进行。台账、链接和差异检查随提交执行。用户修改的分工 Excel 不处理。
