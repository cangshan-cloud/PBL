# CHG-20261018-010：对比导出披露完整数据版本 ID

## 背景与决策

对比逻辑已用 `dataset_version_id` 判断数据版本是否相同，但 CSV 和 HTML 只显示人类可读的版本号。不同数据集都可能使用 `0.2.0` 等相同版本号，离线文件无法据此解释“数据版本不同”的警告，也不足以精确追溯源数据。决定在两种导出中加入已经存在于比较结果中的完整数据版本 ID，同时保留原版本号。只改变导出元数据，不改变比较判定、指标、权限或数据集。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| CSV 主表增加 `dataset_version_id` 列 | `backend/app/services/comparisons.py::comparison_csv` |
| HTML 任务溯源表增加数据版本 ID 与版本号分列 | `backend/app/services/comparisons.py::comparison_html` |
| 两任务 CSV/HTML 完整 ID 回归 | `backend/tests/test_comparisons.py::test_compares_successful_runs_with_baseline_deltas_and_rankings` |
| 口径、索引及四人责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 后端全量 212 项通过；私有真实 A 股样本只读脚本通过，原 CSV SHA-256 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652` 未改；`git diff --check` 通过。全量测试中的 CLI 写入拒绝提示属于预期保护用例，最终状态 `OK`。
- CSV 增加一列，对依赖固定列序号的外部脚本属于格式变化；应按表头读取。HTML 表格列变宽，长 ID 允许换行，但本轮没有浏览器打印视觉验收。
- 版本 ID 是数据库内的精确身份，不替代源文件 SHA-256、来源许可和历史披露时点核查。不形成投资结论。实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
