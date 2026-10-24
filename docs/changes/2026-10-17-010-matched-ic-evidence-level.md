# CHG-20261017-010：严格样本 IC 有效日证据提示

- 日期：2026-10-17
- 类型：研究结果解释与导出
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器人工或 Compose 联调

## 决策过程

上一轮将“至少一个有效 IC 截面”设为严格样本摘要可用的最低条件，但可计算不等于证据充分。为避免 1 个有效日与几十个有效日被读成同等可靠，沿用单任务结论中已有的 20/60 日边界，以**各所选 Run 的最少有效 IC 日数**标注 `insufficient`（1—19）、`limited`（20—59）、`descriptive`（60 及以上）。即使达到 60 日仍不称“显著”或“有效”；这只是描述性提示，不改变原始 IC、排名或 `comparable` 口径标记。全区间和验证期严格样本均展示，旧 Run 缺产物的不可用行为不变。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 最少有效日与证据分层、CSV/HTML 提示 | `backend/app/services/comparisons.py::_matched_ic_summary`、`_ic_evidence`、`comparison_csv`、`comparison_html` |
| 页面分别展示两类严格样本证据提示 | `frontend/src/main.tsx` |
| 边界值及真实运行摘要回归 | `backend/tests/test_comparisons.py::test_ic_evidence_uses_minimum_valid_days_without_claiming_significance`、`test_validation_split_comparison_discloses_mixed_and_different_cutoffs` |
| 研究口径、索引、四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/TIME_SPLIT_VALIDATION.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：207 项通过。
- `frontend` 下 `npm run build && npm test -- --run`：构建及 13 项通过。
- 未做真实 A 股样本新一轮回测、浏览器人工点测或 Compose/Celery 联调。20/60 日是课程产品解释阈值，不是统计检验门槛；样本选择、序列相关与多重试验偏差尚未校正。
