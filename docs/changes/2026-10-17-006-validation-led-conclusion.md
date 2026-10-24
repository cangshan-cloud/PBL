# CHG-20261017-006：验证期主导的规则结论

- 日期：2026-10-17
- 类型：研究解释口径修正
- 执行者：Codex
- 状态：Mac 本机后端自动回归通过；未做浏览器手工或 Compose 联调

## 决策过程

时间切分功能已输出研究期、验证期 IC，但结构化结论仍按**全区间** IC 评级；验证期样本少或方向反转时，全区间较高指标可能掩盖风险。决定带 `time_split` 的任务使用验证期 IC 与有效日数形成标题和评级；全区间 IC、分组收益、成本与换手仅保留为背景证据。验证期不足 20 个有效 IC 日为 `insufficient`；20—59 日或研究／验证方向反转时不得评为 `promising`。不设置切分日的任务保持旧阈值与版本。结论仍是回溯描述，不作前瞻预测或投资建议。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 验证期评分、方向反转提示、全区间背景标注、方法版本与评分依据 | `backend/app/services/conclusions.py::build_run_conclusion` |
| 单元与隔离 HTTP 验证 | `backend/tests/test_conclusions.py::test_time_split_grade_uses_validation_not_full_range`、`backend/tests/test_api_journey.py::test_predeclared_time_split_survives_task_report_and_conclusion` |
| 研究口径 | `docs/TIME_SPLIT_VALIDATION.md`、`docs/RESEARCH_CONCLUSION.md` |
| 四责任包 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：202 项通过。
- 本轮没有改前端代码；沿用上一轮前端 13 项测试与构建成功证据，不伪称本轮重新运行。
- 测试覆盖全区间强但验证期不足、验证期 20—59 日上限、60 日以上评级及研究／验证 IC 方向反转；旧规则 `1.0.2` 仍有回归断言。
- 已保存的旧 HTML 报告不改写；动态结论接口按当前规则解释已有 `time_split`，方法版本为 `1.0.3`。未重新计算真实 A 股市场样本，也未做浏览器人工点测。
