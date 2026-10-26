# CHG-20261026-016 报告逐日表保留诊断独有日期

## 问题与决策

前版核对表只使用 IC、多空及各组净值序列的日期并集。若 `daily_coverage` 已记录一个样本日，但该日所有曲线都没有值，表会漏掉整行，读者难以发现。决定将可用逐日诊断日期并入表的共同轴，并显示当天 IC／分组计算状态；数值仍留空，不补零或前值。旧 Run 无 `daily_coverage` 时维持原有序列并集逻辑；若两者均无日期，则不生成表。不改变研究计算、独立市场日历或既有归档。实际执行者：Codex。

## 修改内容与对应位置

- `backend/app/services/reports.py::_daily_series_detail`：序列与 `daily_coverage` 日期并集；有诊断时追加 IC／分组状态两列，诊断独有日数值为“—”，缺诊断的序列日状态也为“—”；汇总称“已知日期”。
- `backend/app/services/reports.py::COVERAGE_STATUS_LABELS` 与 `build_report_html` 的逐日样本诊断表：共用状态标签映射，维持原有中文含义。
- `backend/tests/test_reports.py::test_report_daily_series_table_joins_dates_without_filling_values`：覆盖诊断独有日期、只有诊断无曲线、旧结果无诊断与空结果。
- `backend/tests/test_api_journey.py::test_upload_publish_research_report_and_role_boundaries`：隔离合成任务的报告逐行比对扩展到全部已知日期和状态列。
- `docs/SINGLE_FACTOR_ANALYSIS.md`、本索引与 A/B/C/D 四责任包：说明日期与状态的可解释边界。

## 验证与未决事项

定向单测与 API 闭环通过；后端 293 项、前端 80 项、前端构建及黄金样例通过；台账和链接检查见本轮提交。没有启动容器或浏览器，本轮未重验窄屏新增状态列；此前浏览器仅覆盖旧列数。状态为已有计算诊断，不足以单独归因停牌、预热、缺行情或财务披露。若全部序列和诊断都没有某市场日，仍无法凭该表恢复独立交易日历；旧归档不回写，队长本人产品实测待完成。
