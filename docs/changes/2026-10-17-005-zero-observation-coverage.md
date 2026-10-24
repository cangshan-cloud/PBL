# CHG-20261017-005：候选证券覆盖与零观测日期

- 日期：2026-10-17
- 类型：研究数据质量诊断
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器手工或 Compose 联调

## 决策过程

上一轮 `daily_coverage` 只遍历已经形成观测的日期；整天没有可检验因子／次日收益时完全不显示，容易误以为日期不存在。决定以任务筛选前确定的完整数据集市场日期作为普通 CSV 日历，并以**已筛选证券的当日原始行数**为候选数；历史包以当日历史成员为候选数。将 `evaluate` 的有效观测逐日对齐，补零观测日期与候选、有效、差额、比例；候选为零时比例为不可计算。差额不具备具体排除原因，故 UI、报告和结论均不臆测停牌或缺行。原有 IC、分组指标和跳过计数不变。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 候选日历与有效观测对齐、比例、零观测日、合计核对 | `backend/app/services/coverage.py::enrich_daily_coverage` |
| 普通和历史任务接入候选来源 | `backend/app/services/runs.py::execute_research_run` |
| 工作台与 HTML 报告逐日表及总体覆盖摘要 | `frontend/src/main.tsx` 研究结果区、`backend/app/services/reports.py::build_report_html` |
| 结论限制中披露零观测日 | `backend/app/services/conclusions.py::build_run_conclusion` |
| 口径文档与测试 | `docs/SINGLE_FACTOR_ANALYSIS.md`、`backend/tests/test_coverage.py`、`backend/tests/test_api_journey.py`、`backend/tests/test_reports.py` |
| 四责任包同步 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：201 项通过。
- `npm run build`、`npm test -- --run`：构建及 13 项测试通过。
- 隔离 HTTP 测试覆盖候选有记录但无有效标签、选定证券当日零记录；后者比例为 `null`。后端纯函数测试覆盖数值对账与有效数超过候选时拒绝。
- 本轮未重新采集真实市场数据、未做浏览器手工点测、未启动 Compose/Celery。用户原有 Excel 修改未触碰。
