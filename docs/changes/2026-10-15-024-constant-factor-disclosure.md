# CHG-20261015-024：工作台与结论披露全同值跳过日期

- 日期：2026-10-15
- 类型：disclosure + UI + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

[上次修正](2026-10-15-023-constant-factor-no-signal.md)让全截面因子同值日不再生成伪分组收益，HTML 报告已提示跳过天数，但研究工作台与动态结构化结论未披露。若用户只看页面或结论，会误以为所有日期都进入分组。决定直接读取新结果字段 `group_skipped_constant_factor_days`，仅在正数时提示；对旧 Run 缺失字段不反推、不改写。结论只增加限制说明，不改阈值或等级规则。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 类型及研究结果提示 | `frontend/src/main.tsx::Result`、研究工作台结果区 | 直观看到无信号日期的处理 |
| 结论限制说明 | `backend/app/services/conclusions.py::build_run_conclusion` | 任务中心与新报告草稿说明分组样本范围 |
| 新旧结果回归及报告计数断言 | `backend/tests/test_conclusions.py::ConclusionTests`、`backend/tests/test_reports.py::ReportTests` | 避免旧数据缺字段出错 |
| 文档口径 | `docs/RESEARCH_CONCLUSION.md::判定规则` | 明确不改变分档 |
| 总索引 | `docs/CHANGE_INDEX.md` | 决策可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：166 项通过。
- `npm run build --prefix frontend`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

旧 HTML 报告保持不可变；动态结论会按当前规则渲染，但旧指标缺少跳过计数时不会显示该项。前端仅展示跳过总数，逐日详情仍需查看 IC 序列和结果数据；这不等于真实持仓或可成交回测。
