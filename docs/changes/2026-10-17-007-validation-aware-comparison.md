# CHG-20261017-007：实验对比披露验证期 IC

- 日期：2026-10-17
- 类型：研究对比口径与展示
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器手工或 Compose 联调

## 决策过程

单任务结论已改为验证期主导，但实验对比仍只展示全区间排名，容易把带切分与不带切分的结果误作同口径比较。选择保留原排名与差值以兼容旧 Run，新增**已保存**验证期 IC 摘要，不隐式计算新的验证期排名。混用切分、不同起始日、参数与产物不符及同切分日有效日期不同时给出风险提示。只有切分日相同才报告共同验证期有效 IC 日数；旧任务的验证期字段留空而非填零。该摘要不做验证期逐股同样本重算，不宣称可交易收益。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 分段摘要读取、切分口径检查、共同验证期有效日数 | `backend/app/services/comparisons.py::compare_runs` |
| CSV 列及 HTML 独立章节 | `backend/app/services/comparisons.py::comparison_csv`、`comparison_html` |
| 对比页独立验证期表、原排名标签 | `frontend/src/main.tsx` |
| 混合切分、不同切分日、相同切分日、导出与 JSON 回归 | `backend/tests/test_comparisons.py::test_validation_split_comparison_discloses_mixed_and_different_cutoffs` |
| 研究口径与四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/TIME_SPLIT_VALIDATION.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：203 项通过。
- `frontend` 下 `npm run build && npm test -- --run`：构建与 13 项测试通过。
- 未重新采集真实 A 股样本；没有运行 Compose/Celery 或浏览器人工点测。验证期摘要仍可能受股票池、预处理、标签口径影响，不能作为投资结论。
