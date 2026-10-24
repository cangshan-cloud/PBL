# CHG-20261018-016 对比 CSV 摘要行安全写出

## 问题与决策

对比 CSV 的任务指标行已用 `csv.DictWriter` 和表格公式防护，但“证据提示”“严格样本不可用原因”等摘要行仍直接拼接字符串。提示若含逗号、引号或换行，表格列会错位；若以公式触发字符开头，还可能被表格软件解释为公式。决定沿用现有 `_spreadsheet_safe` 策略，将全部摘要行交给同一个 `csv.writer` 写出，不改变指标计算、接口结构或原始记录。

## 修改位置

- `backend/app/services/comparisons.py`：在 `comparison_csv` 增加 `section_row`，统一对摘要标签和值做公式防护及 CSV 转义；指标行和 HTML 保持原路径。
- `backend/tests/test_comparisons.py`：新增含公式前缀、引号、逗号、换行和前导制表符的摘要文本回归，以 `csv.reader` 验证仍为两个单元格。
- `docs/EXPERIMENT_COMPARISON.md`：说明安全写出覆盖整个 CSV，而非仅任务指标行。
- `docs/CHANGE_INDEX.md` 与 A/B/C/D 责任包：同步记录本次变更和验收边界。

## 验证与边界

新增定向测试通过；后端 `python -m unittest discover -s backend/tests` 共 213 项通过。此次是导出编码稳健性修复，不代表能将任意 CSV 当成单一规则矩形表：文件本身仍由任务明细和若干摘要区组成。未修改真实行情数据、研究公式或前端，也未在本轮重新进行浏览器下载。实际执行者：Codex。
