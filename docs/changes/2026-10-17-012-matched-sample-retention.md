# CHG-20261017-012：严格样本交集保留率披露

- 日期：2026-10-17
- 类型：研究样本可解释性
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器人工或 Compose 联调

## 决策过程

最少有效 IC 日数能提示时间长度，却不能说明严格样本交集相对原任务缩小了多少；共同证券很少时，长期 IC 也可能只代表狭窄股票池。决定对全区间和验证期严格样本分别披露每个 Run 的“共同证券日期观测数 ÷ 该 Run 原有效观测数”，不改动已保存指标，也不设置缺乏依据的统一保留率门槛。旧指标分母缺失或为零时显示空值；比率大于 100% 则作为产物口径不一致风险提示。该比率不是股票覆盖率、有效 IC 日期比例或投资有效性评分。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 各 Run 原观测分母、保留率、异常口径提示 | `backend/app/services/comparisons.py::compare_runs`、`_matched_ic_summary` |
| CSV 两类严格摘要列、HTML 保留率行 | `backend/app/services/comparisons.py::comparison_csv`、`comparison_html`、`_retention_html_rows` |
| 对比页共同样本保留率表 | `frontend/src/main.tsx` |
| 回归与黄金样本 | `backend/tests/test_comparisons.py::test_retention_over_one_warns_about_inconsistent_saved_counts` 及现有严格样本用例、`backend/tests/test_matched_comparison_golden.py`、`docs/MATCHED_COMPARISON_GOLDEN.md` |
| 口径、总索引及四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/TIME_SPLIT_VALIDATION.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：209 项通过。
- `frontend` 下 `npm run build && npm test -- --run`：构建及 13 项通过。
- 未重新采集真实 A 股数据、未做浏览器人工或 Compose/Celery 联调。保留率对观测条数敏感；不能据此推断行业、市值或交易可达性覆盖。
