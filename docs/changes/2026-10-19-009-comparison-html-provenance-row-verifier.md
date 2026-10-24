# CHG-20261019-009 HTML 对比溯源逐任务核对

## 问题与决策

离线校验器原先只检查每个身份值是否在 HTML 全文出现。若报告把两个任务的 Run ID 或数据哈希放错行，各值仍在全文中，可能被误判为一致。决定解析报告首张“任务溯源”表，按 JSON 的任务顺序逐行核对角色、实验名、完整 Run ID、数据版本 ID、SHA-256、版本号和代码版本；不改变导出格式或研究计算。

## 修改位置

- `tools/verify_comparison_exports.py`：使用标准库 `HTMLParser` 读取首张表的 tbody，每个任务必须恰有七个单元格，并逐行与 JSON 匹配。后续核心指标和警告检查保持原有范围。
- `backend/tests/test_comparison_export_verifier.py`：新增单行哈希错配、两任务 Run ID 换行的反例；原合法导出仍通过。
- `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、A/B/C/D 四责任包：更新校验能力与边界。实际执行者：Codex。

## 验证与边界

定向测试通过，后端全量 214 项通过；上一轮浏览器实际下载的同组 JSON/CSV/HTML 在新校验器下仍返回 2 任务、2 警告、CSV/HTML 均通过。

这是导出一致性检查。它不提供独立数据来源证明、签名或因子公式复算；同步伪造三文件仍可能通过。
