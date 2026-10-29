# CHG-20261029-005 成分同样本 IC 原值 CSV 导出

## 问题与决策

研究员可在工作台、任务中心和 HTML 报告查看成分 IC，但页面展示四位小数，团队独立核对完整原值需要读取复现包。决定在任务中心为已保存 `component_ic` 的 Run 增加只读 CSV 导出，包含完整 Run ID、因子键、原始 IC/Rank IC、有效日期数、信号日期数和共同覆盖量；旧 Run 缺字段时不显示按钮。CSV 使用现有单元格转义和公式防护。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 原值 CSV 与文件名 | `frontend/src/component-ic-export.ts::componentIcCsv`、`componentIcFilename` | 输出可由完整 Run 身份追溯的机器可读摘要 |
| 任务中心条件下载按钮 | `frontend/src/main.tsx` 任务详情 `task-component-ic` 区 | 新 Run 可下载，旧 Run 不产生误导性空表 |
| 原值、空值、身份和公式防护测试 | `frontend/tests/component-ic-export.test.ts`、`frontend/package.json` | 固定导出格式及安全边界 |
| 口径、真实下载证据、总索引与四责任包 | `docs/MULTI_FACTOR_ANALYSIS.md`、`docs/HISTORICAL_COMPONENT_IC_CSV_QA_2026-10-29.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 保留决策、代码位置和验收 |

## 验证与未决事项

Mac 前端 88 项测试和生产构建通过。隔离浏览器实际下载新 Run CSV，四行全精度指标和 72,366 条共同覆盖量与前轮真实样本一致；旧 Run 无按钮，控制台 0 error/0 warning。隔离项目关闭后主 `fbl` 仍 `running(5)`。本轮未改变后端或重跑后端测试，未做队长人工实测、Windows 和数据来源授权核验。台账、链接及差异检查随提交执行；用户修改的分工 Excel 不处理。
