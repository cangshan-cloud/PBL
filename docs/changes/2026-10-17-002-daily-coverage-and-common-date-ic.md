# CHG-20261017-002：逐日样本诊断与共同日期 IC 摘要

- 日期：2026-10-17
- 类型：研究解释性与对比口径改良
- 执行者：Codex；用户本轮明确暂不考虑演示与 Windows
- 状态：Mac 本机自动回归通过；未做浏览器手工验收或真实市场投资效力检验

## 决策过程

已有 `coverage` 总数和两类分组跳过天数，但研究者无法定位哪天样本不足；对比只统计共同日期，不提供同期 IC 摘要。决定从研究引擎现有的有限观测记录逐日有效证券数和 IC／分组状态；从不可变 Run 逐日 IC 序列计算共同有效 IC 日期上的摘要，不改写原始指标、差值与排名。没有逐股共同样本和完整换手路径，故不重算逐股 IC、多空净值与成本，不称为完整同样本比较。上游数据排除原因仍须由数据质量或历史审计解释。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 保存每个有观测因子日的有效证券数及 IC、分组状态 | `backend/app/domain/research.py::evaluate` |
| 工作台逐日表、HTML 报告中的诊断范围说明 | `frontend/src/main.tsx` 研究结果区、`backend/app/services/reports.py::build_report_html` |
| 对共同有效 IC 日期重算四项 IC 摘要，单独输出到 JSON、CSV、HTML | `backend/app/services/comparisons.py::compare_runs`、`comparison_csv`、`comparison_html`、`frontend/src/main.tsx` 实验对比区 |
| 口径与局限说明 | `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/EXPERIMENT_COMPARISON.md` |
| 回归测试 | `backend/tests/test_research.py::test_daily_coverage_discloses_engine_skip_reasons`、`backend/tests/test_comparisons.py` |
| 四人责任包同步 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：192 项通过。
- `npm test -- --run`：13 项通过；`npm run build`：通过。
- 系统 `python3` 缺少 SQLAlchemy，不能用于完整回归；已改用项目 `.venv`，不是代码缺陷。
- 本轮未启动 Compose/Celery、未做浏览器人工点测、未获取新真实样本。四份验收材料均记录为开发者代执行的自动化证据，不冒充四位成员手工操作。
