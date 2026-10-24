# CHG-20261017-009：严格样本 IC 空交集与不可计算状态

- 日期：2026-10-17
- 类型：对比结果正确性与空状态
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器人工或 Compose 联调

## 决策过程

验证期严格样本已经对无共同证券日期键降级，但全区间严格样本仍可能在交集为空时返回 `available=true`；有共同键但因子截面全同值或数量不足、任一任务无有效 IC 日期时，也可能显示“可用”而数值全空。决定以**每个任务至少有一个有效 IC 截面**作为严格摘要可用的最低条件，并在全区间和验证期一致执行。若交集为空或不满足最低条件，保留原始指标，严格摘要返回原因并添加可比性警告。此处只判断能否计算，不以 1 日 IC 宣称统计可靠；未更改因子或 IC 公式。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 全区间空交集、有效 IC 日检查与可比性警告；验证期同规则 | `backend/app/services/comparisons.py::compare_runs`、`_matched_ic_summary` |
| 空交集与全同值因子观测回归 | `backend/tests/test_comparisons.py::test_validation_matched_sample_requires_shared_symbol_dates`、`test_matched_sample_requires_valid_ic_cross_sections` |
| 口径说明及四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：206 项通过。
- `frontend` 下 `npm run build && npm test -- --run`：构建及 13 项通过；本轮未修改页面组件，既有不可用原因呈现路径复用。
- 单项 IC 有效日并不代表可靠性；严格摘要可用也不消除价格、收益标签、预处理和样本外选择偏差。未重新采集真实 A 股数据，也未做浏览器人工或 Compose 联调。
