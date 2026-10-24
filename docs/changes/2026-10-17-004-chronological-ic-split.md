# CHG-20261017-004：预设日期的研究期／验证期 IC 诊断

- 日期：2026-10-17
- 类型：研究流程与解释边界
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器手工或 Compose 联调

## 决策过程

此前只有全区间和跨 Run 对比，缺少同一 Run 的时间分段检验。决定让研究人员**运行前**指定验证期起始日，按信号日期分开统计 IC；边界前最近一个信号日隔离，避免其下一市场日收益进入研究期。只输出 IC 类摘要，不把分段组合收益误说成可交易验证。切分日期可由人反复改动，因此 UI、报告和结论都将其限定为回溯诊断，不宣称天然前瞻样本外有效。该功能先覆盖普通单因子与等权组合，历史固定模式保持原口径。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 切分、隔离、最短阶段检查与 IC 摘要 | `backend/app/domain/time_split.py::evaluate_time_split` |
| 请求参数、日期校验及普通/组合任务落库结果 | `backend/app/schemas.py`、`backend/app/services/runs.py::_normalize_sample_parameters`、`execute_research_run` |
| 工作台输入、提交前校验、结果归属与分段表 | `frontend/src/research-config.ts`、`frontend/src/main.tsx` |
| HTML 报告与规则结论的分段证据和限制 | `backend/app/services/reports.py::build_report_html`、`backend/app/services/conclusions.py::build_run_conclusion` |
| 回归 | `backend/tests/test_time_split.py`、`backend/tests/test_api_journey.py`、`frontend/tests/research-config.test.ts` |
| 口径与团队验收 | `docs/TIME_SPLIT_VALIDATION.md`、`docs/CHANGE_INDEX.md`、A/B/C/D 四责任包 |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：199 项通过。
- `npm run build`、`npm test -- --run`：构建和 13 项测试通过。
- 隔离 HTTP 测试核对全区间原指标不变、分段结果进入任务/报告/结论；纯函数测试核对边界隔离。
- 未在真实市场上证明预测力，未做浏览器手工验收、Celery/Compose 联调。用户工作区原有 Excel 修改未触碰。
