# CHG-20261014-014：多因子 HTML 报告收录因子相关矩阵

- 日期：2026-10-14
- 类型：product report + tests + evidence
- 状态：implemented / verified on macOS OrbStack
- 关联提交：与本记录同次提交

## 背景与目标

PRD 要求研究报告包含因子相关性。多因子计算已将共同样本上的逐日截面相关矩阵存入结构化结果，工作台也展示该数据，但下载的 HTML 报告只列组合成分和共同覆盖量，缺少相关矩阵。报告作为课程验收产物因此不完整。

## 决策过程

复用任务结果中已保存的 `composite.correlation_matrix`，按照实验记录中的因子顺序生成方阵；不在报告生成阶段重新计算，以保证页面、结构化结果和报告同源。表格说明它是有效日期的截面 Pearson 相关均值，空值用“—”，并明确不代表因果或独立增益。所有因子标识经 HTML 转义。仅影响新报告，旧文件遵守不可变原则。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 在多因子报告的组合成分后呈现相关方阵及解释 | `backend/app/services/reports.py::build_report_html` | 报告具备 PRD 要求的因子相关性证据 |
| 普通多因子、历史四因子及 HTML 转义/空值测试 | `backend/tests/test_composite.py`、`backend/tests/test_historical_task.py`、`backend/tests/test_reports.py` | 防止报告缺失或注入回归 |
| 更新多因子与历史包使用说明 | `docs/MULTI_FACTOR_ANALYSIS.md`、`docs/HS300_BUNDLE.md` | 对齐输出和解释边界 |
| 登记本次变更 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `make test`：124 项通过，包含矩阵呈现、四因子报告、特殊字符转义和空值。
- 独立 OrbStack 项目 `factorlab-hs300-report-qa` 使用本机私有包经 Redis/Celery 完成任务 `3876d40c-ba93-49a7-8288-a8cfbe3ce953`，审计导出核对为 4 因子、968 行逐日、32 条无标签信号。研究员身份下载新 HTML 报告返回 HTTP 200、44,244 字节，相关矩阵出现一次，四个对角线单元格为 `1.0000`。
- 隔离项目容器、网络和专用数据库卷已删除；证据目录在 `/private/tmp/fbl-hs300-report-qa-evidence/`，不进入 Git。主 `fbl` 项目未用于此任务。
- 随后只重建并替换主 `fbl` 的 API/Worker，Web、PostgreSQL、Redis 未替换。宿主机页面、数据文件、账号及 Worker 只读预检通过；主库任务仍为 26 条，26 份既有 HTML 报告校验和均通过。

## 风险、回退与未决事项

矩阵是已保存的样本内相关性摘要，不证明因子独立收益贡献。旧 HTML 报告不会重写，仍可通过结构化结果或复现包查看相关矩阵。此次未做 Windows、浏览器打印分页或多人并发测试。
