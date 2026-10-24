# CHG-20261017-013：指标与逐股观测产物计数核对

- 日期：2026-10-17
- 类型：结果产物一致性诊断
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器人工或 Compose 联调

## 决策过程

交集保留率的分母取已保存指标，但仅在交集超过分母时报警；如果指标分母大于逐股观测产物条数，比例仍可能看起来正常。确认正常任务的 `coverage` 等于完整逐股观测条数，`time_split.validation.observation_count` 等于产物在切分日及以后的条数。决定比较时直接核对这两组计数，任何方向不等都发出风险提示，并在 API、CSV、HTML、页面披露产物计数。缺少旧产物则保持空值；不改写不可变 Run，也不以通过条数核对冒充内容完全一致。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 全区间／验证期逐股产物计数及双向不一致提示 | `backend/app/services/comparisons.py::compare_runs` |
| CSV 元数据列、HTML 摘要行 | `backend/app/services/comparisons.py::comparison_csv`、`comparison_html` |
| 页面保留率表并列原观测与产物观测 | `frontend/src/main.tsx` |
| 正常计数、指标偏大／偏小及导出回归 | `backend/tests/test_comparisons.py::test_validation_split_comparison_discloses_mixed_and_different_cutoffs`、`test_retention_over_one_warns_about_inconsistent_saved_counts` |
| 口径、索引、四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/TIME_SPLIT_VALIDATION.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：209 项通过。
- `frontend` 下 `npm run build && npm test -- --run`：构建及 13 项通过。
- 未重新采集真实 A 股数据、未做浏览器人工或 Compose/Celery 联调。条数一致不能证明因子值、标签、披露时点或数据许可正确。
