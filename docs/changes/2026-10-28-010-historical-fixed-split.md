# CHG-20261028-010 历史沪深300固定 7 月时间切分诊断

## 问题与决策

历史模式已有全年 IC、分组和报告，但普通研究的研究期／验证期诊断没有进入历史任务。课程验收需要更清楚地区分区间内拟合描述和后段检验。选择**可选固定 2024-07-01**，不用任意日期输入，以便团队使用同一口径；隔离边界前最后一个信号日，保持全年原始指标不变。原历史固定四因子、窗口、等权、成本设置均不变。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 历史请求只接收固定切分日，任务存参并生成 `time_split` | `backend/app/schemas.py::HistoricalResearchRequest`、`backend/app/services/runs.py::create_historical_run`、`execute_research_run` | 固定可复现的研究/验证口径 |
| 历史同包复算支持并严格核对切分参数 | `tools/verify_historical_recomputation.py::recompute_result`、`verify_recomputation` | 防止新任务无法离线复验 |
| 私有隔离新 Run 支持切分选项 | `tools/run_isolated_historical_replay.py::run_isolated_replay` | 在 Mac 上对真实包验证新路径 |
| 历史工作台勾选与配置键 | `frontend/src/research-config.ts::buildResearchConfiguration`、`frontend/src/main.tsx` 历史模式、`frontend/src/layout.css` | 让研究员可明确选择，改配置后隐藏旧结果 |
| 构造 HTTP／复算与前端配置回归 | `backend/tests/test_api_journey.py`、`backend/tests/test_historical_recomputation.py`、`frontend/tests/research-config.test.ts` | 锁定非法日期、隔离边界、报告结论与全区间不变 |
| 口径、证据及四责任包 | `docs/TIME_SPLIT_VALIDATION.md`、`docs/HISTORICAL_FIXED_SPLIT_QA_2026-10-28.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 保留决策与实际验收范围 |

## 验证与未决事项

构造 HTTP、复算和前端配置目标测试通过；Mac 后端全量 327 项、前端 86 项与生产构建、黄金指标通过。私有封存包内存新 Run、严格 V2 导出/报告、同包复算及 242 日结果一致性通过，研究 116 日、验证 125 日，隔离 2024-06-28。变更台账、链接与差异检查随提交执行。未重建主 Compose、未浏览器实点新控件、未做队长人工验收；固定日期的历史回溯不能称为前瞻样本外，也不认证原始数据授权。用户修改的分工 Excel 不处理。
