# CHG-20261016-009：实验对比 CSV 文本公式防护

- 日期：2026-10-16
- 类型：export safety + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

实验对比 CSV 面向 Excel 等表格软件，导出字段包含已保存的实验元数据和风险提示。正常创建的实验名称由系统生成，目前没有证据表明普通请求可直接注入公式；但历史或异常元数据若以 `=`、`+`、`-`、`@` 等字符开头，表格软件可能将文本当作公式。决定仅在 CSV 文本单元格导出边界加单引号，保留前导空白与原始内容；不改数据库、JSON、HTML 或数值指标。历史审计 CSV 有独立复现校验契约，本次不改其格式。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 文本单元格公式中和 | `backend/app/services/comparisons.py::_spreadsheet_safe`、`comparison_csv` | 对比行及风险提示不再被表格软件当作公式 |
| 异常元数据回归 | `backend/tests/test_comparisons.py::ComparisonTests.test_csv_neutralizes_formula_like_saved_metadata` | 验证引号、制表符、前导空白及原值不变 |
| 导出说明 | `docs/EXPERIMENT_COMPARISON.md` | 明确 CSV 与 JSON 口径区别 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯本次决定 |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_comparisons -q`：10 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：181 项通过；其中隔离写入确认的负面用例会预期输出命令行错误文字，但测试进程退出码为 0。
- `git diff --check`：通过。

## 风险、回退与未决事项

如果后续用程序读取 CSV 文本字段，开头可能多一个单引号；需要无损原值应使用 JSON 接口。防护针对常见电子表格公式前缀，不替代文件来源与完整性检查。Windows/Excel 人工打开验证尚未完成。
