# CHG-20261017-011：严格同样本 IC 手算黄金样本

- 日期：2026-10-17
- 类型：独立指标验算与课程验收证据
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做真实 A 股新样本或 Compose 联调

## 决策过程

严格同样本对比已有接口、导出、降级和边界测试，但其数值测试主要复用平台计算结果或仅断言非空，不能独立证实 IC/Rank IC/ICIR 的值。根据现有课程范围与扩展项取舍，优先增加一个**不依赖平台生成期望值**的 3 日 × 3 股手算黄金样本，而不是扩大研究功能。固定两 Run 相反的每日 IC、单 Run 独有极端观测与相同收益标签，验证交集筛选及指标正负号；不修改生产算法或历史 Run。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 独立期望值及自动回归 | `backend/tests/test_matched_comparison_golden.py::MatchedComparisonGoldenTests.test_three_date_intersection_matches_hand_derived_ic` |
| 原始输入、手算公式与解释边界 | `docs/MATCHED_COMPARISON_GOLDEN.md` |
| 验收矩阵、总索引、四责任包 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：208 项通过；新黄金用例单独通过。
- `frontend` 下 `npm run build && npm test -- --run`：构建及 13 项通过；本轮未改前端功能。
- 这是单元层的手算检验，不是私有真实行情复核、跨环境 CI 或浏览器人工验收；三日 IC 的证据等级为 `insufficient`。
