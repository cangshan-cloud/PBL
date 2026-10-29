# CHG-20261029-002 等权组合成分因子同样本 IC 诊断

## 问题与决策

原多因子结果展示权重和相关矩阵，却没有说明各成分在合成**共同有效样本**上与次日收益的关系。决定增加只读描述性诊断，不调整权重、不按结果翻转方向，也不改变组合因子值、分组或全区间 IC。各成分继续先在自身原始可用截面预处理，再于已对齐的共同证券日期取值；这样诊断对应实际合成输入。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 共同样本逐日 IC、Rank IC 和有效日期汇总 | `backend/app/domain/composite.py::combine_factor_observations` | 让成分诊断与真实合成输入同口径 |
| 新 Run HTML 报告表格及字段转义 | `backend/app/services/reports.py::build_report_html` | 报告保留相同证据且防止标签注入 |
| 工作台表格与旧 Run 缺字段状态 | `frontend/src/main.tsx::CompositeResult`、研究结果区 | 研究员可读，旧归档不误显为零 |
| 合成、常数日、交集外证券及报告回归 | `backend/tests/test_composite.py`、`backend/tests/test_reports.py` | 固定计算和展示边界 |
| 口径、私有样本结果、索引和四责任包 | `docs/MULTI_FACTOR_ANALYSIS.md`、`docs/HISTORICAL_COMPONENT_IC_QA_2026-10-29.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 保留决策、证据和工作量记录 |

## 验证与未决事项

Mac 后端 328 项、前端 86 项与生产构建通过；私有 2024 新 Run 的四成分各有 242 有效 IC 日，严格 V2 导出、报告与同包复算通过。台账、链接和差异检查随提交执行。未在浏览器实点新表，旧报告不回写，来源授权、因子独立增益及交易收益不可由本统计推出。用户改动的分工 Excel 不处理。
