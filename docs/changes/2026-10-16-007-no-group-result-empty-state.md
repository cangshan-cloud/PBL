# CHG-20261016-007：无可分组结果的明确空态

- 日期：2026-10-16
- 类型：research empty-state disclosure
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

稀疏样本 HTTP 验收证明任务可成功且 IC 仍可计算，但所有日期都可能无法形成分组。原工作台分组区留空，HTML 表格无行；结论草稿则写“累计收益为无法计算”，容易被忽略或误读成零收益。决定让三处都明确说明没有可计算的分组/多空结果，不修改 IC、分组算法或已保存任务。结论模板版本由 `1.0.1` 升至 `1.0.2`，只变更缺失结果的表述，不变更分档阈值。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 缺失多空证据与限制、模板版本 | `backend/app/services/conclusions.py::build_run_conclusion` | 不将缺失描述为收益表现 |
| 空分组表格占位行 | `backend/app/services/reports.py::build_report_html` | 报告打印时仍可见缺失原因 |
| 工作台空态 | `frontend/src/main.tsx` 研究结果区 | 页面不再只留空白 |
| 单元与稀疏 HTTP 回归 | `backend/tests/test_conclusions.py`、`backend/tests/test_reports.py`、`backend/tests/test_api_journey.py` | 核对全链路口径 |
| 文档与总索引 | `docs/RESEARCH_CONCLUSION.md`、`docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/CHANGE_INDEX.md` | 记录版本与边界 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：179 项通过。
- `npm run build --prefix frontend`：通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

动态结论接口对旧 Run 使用新版措辞，但旧 HTML 报告文件仍不可变；引用时需记录报告生成时的代码与规则版本。页面空态只解释无分组结果，不构造零收益、现金仓位或可交易回测。Windows 浏览器与正式演示仍需实际验收。
