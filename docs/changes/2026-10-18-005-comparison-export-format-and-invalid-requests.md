# CHG-20261018-005：对比页面与 HTML 数值格式一致、异常导出同口径拒绝

## 背景与决策

对比页的 IC／ICIR 显示 4 位小数，但 HTML 导出只保留 2 位，较小差异可能在报告中被四舍五入得不可见；页面“有效观测”差值还显示为 `-300.0000`，与 HTML 的整数单位不一致。CSV 始终保留原始数值，不应为了排版降低机器可用精度。决定只统一页面与 HTML 的显示精度：非百分比连续指标 4 位，百分比 2 位，观测数按整数／原数值显示；差值显式带符号。并把重复 Run ID 对比请求在 JSON、CSV、HTML 三个 HTTP 出口同为 400 的约束纳入回归。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| HTML 非百分比指标及差值显示 4 位，观测数和百分比规则不变 | `backend/app/services/comparisons.py::_export_number` |
| 页面原始对比表差值按单位格式化 | `frontend/src/comparison-format.ts::comparisonDelta`、`frontend/src/main.tsx` 实验对比表 |
| HTML 格式与 HTTP 三出口重复 ID 拒绝测试 | `backend/tests/test_comparisons.py::test_html_numbers_keep_ic_precision_and_count_units`、`test_compares_successful_runs_with_baseline_deltas_and_rankings`、`backend/tests/test_api_journey.py::test_comparison_api_and_exports_include_actual_group_dates` |
| 前端格式测试和测试入口 | `frontend/tests/comparison-format.test.ts`、`frontend/package.json` |
| 文档与四责任包 | `docs/EXPERIMENT_COMPARISON.md`、本文件、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 后端 210 项、前端 23 项及生产构建通过；私有真实 A 股样本只读脚本再次通过，原样本哈希未改。
- 重复 ID 请求的 JSON 对比、CSV 导出和 HTML 导出均为 HTTP 400；不是返回一份看似有效的文件。
- 这是显示格式与异常回归，不改变原 Run、比较指标、CSV 原始数值或投资解释。小数位显示仍会四舍五入；精确复算应使用 JSON／CSV 原数值。
- 本轮未新增浏览器下载点击、HTML 打印排版、Compose/Celery 或 Windows 验收。实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
