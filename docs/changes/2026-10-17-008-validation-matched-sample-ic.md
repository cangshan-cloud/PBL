# CHG-20261017-008：验证期共同证券日期严格样本 IC

- 日期：2026-10-17
- 类型：研究对比证据增强
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器人工或 Compose 联调

## 决策过程

上轮新增的验证期 IC 摘要各自基于原 Run 股票样本，不能隔离样本交集差异。决定在**全部任务预设同一验证期起始日、参数与已存结果一致、逐股观测产物可校验且存在验证期共同键**时，额外取共同“信号日期 × 证券”键重算 IC；原始全区间指标和各 Run 保存的验证期摘要保持不变。重算沿用各 Run 原预处理参数，披露共同观测与收益标签差异；不同数据、价格、收益标签或代码版本仍不能直接因果归因。混切分、不同切分日、旧 Run 无观测产物时明确降级，而不是填零或伪造可比结果。不新增验证期排名或交易收益。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 复用严格样本重算逻辑，增加验证期交集、可用性及标签差异提示 | `backend/app/services/comparisons.py::compare_runs`、`_matched_ic_summary` |
| CSV/HTML 独立验证期严格样本章节 | `backend/app/services/comparisons.py::comparison_csv`、`comparison_html` |
| 页面独立验证期严格样本表 | `frontend/src/main.tsx` |
| 单元与隔离 HTTP 回归 | `backend/tests/test_comparisons.py::test_validation_split_comparison_discloses_mixed_and_different_cutoffs`、`test_validation_matched_sample_requires_shared_symbol_dates`、`backend/tests/test_api_journey.py::test_validation_matched_comparison_is_available_through_http_and_exports` |
| 口径、索引和四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/TIME_SPLIT_VALIDATION.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：205 项通过，含无共同证券日期降级、隔离 HTTP 对比及 CSV/HTML 导出。
- `frontend` 下 `npm run build && npm test -- --run`：构建及 13 项通过。
- 未重新采集真实 A 股样本、未运行 Compose/Celery、未做浏览器人工点测。严格样本 IC 是历史回溯研究指标，不是显著性或未来收益证明。
