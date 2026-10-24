# CHG-20261018-008：HTML 对比报告补齐任务溯源

## 背景与决策

上一轮浏览器保存文件名改为含 Run 短 ID，但 HTML 报告正文只有任务名称和因子键。同名实验、文件重命名或转交后，短文件名不足以独立追溯来源；`docs/EXPERIMENT_COMPARISON.md` 声称 HTML 内有完整 Run ID，与实际不符。决定在报告开头添加按选择顺序排列的任务溯源表，披露基准/候选角色、实验名、完整 Run ID、数据版本和代码版本。CSV 已有完整 ID，不改其格式；HTML 新文本均转义，避免把保存的元数据当作标记执行。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 任务溯源表及长代码换行样式 | `backend/app/services/comparisons.py::comparison_html` |
| 完整 ID、顺序、角色与 HTML 转义回归 | `backend/tests/test_comparisons.py::test_compares_successful_runs_with_baseline_deltas_and_rankings` |
| 口径、索引及四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 定向对比模块 18 项、后端全量 210 项通过；`git diff --check` 通过。全量测试中的 CLI 安全拒绝提示来自预期的保护测试，最终状态为 `OK`。
- 新表中的完整 Run ID 在 HTML 转义后出现，顺序与基准/候选角色一致；恶意实验名中的 `<script>` 不会作为原始标签出现。
- 不改变对比指标、CSV/JSON、任务和报告持久化，也不增加用户可访问的任务范围。长 ID 已允许在单元格换行，但本轮未做浏览器打印视觉验收；不能据此宣称分页完善。
- 实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
