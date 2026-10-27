# CHG-20261027-007 逐日样本诊断 CSV 离线核对

## 问题与决策

每日 IC、多空、分组净值 CSV 已可对同 Run 复现 JSON 离线逐行核对；浏览器导出的逐日样本诊断 CSV 尚无同等检查。决定扩展现有只读工具，核对其表头、行序、完整 Run ID、候选/有效/排除数、原始覆盖率及 IC/分组状态；缺字段对应空单元格，不以零替换。保持“同源一致性”定位，不把复现包哈希说成签名或对原始行情的独立验算。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_series_exports.py::verify_series_exports`：新增 `--daily-coverage-csv` 及 `daily_coverage_rows` 摘要，复用复现结果哈希与逐行字段比较；旧的三类参数保持兼容。
- `backend/tests/test_series_exports.py`：覆盖诊断 CSV 正例、错 Run、缺行、状态/覆盖率/表头篡改、空值被零替换、复现包缺诊断序列。
- `docs/SERIES_EXPORT_VERIFICATION.md`、[四文件只读核对](../DAILY_COVERAGE_EXPORT_OFFLINE_QA_2026-10-27.md)、`docs/SINGLE_FACTOR_ANALYSIS.md`、本索引和 A/B/C/D 四责任包：说明用法、执行文件、证据边界。

## 验证与未决事项

10 项定向测试通过；留存的同 Run 复现 JSON 与四份浏览器下载 CSV 一次只读核对输出 IC 242、多空 242、分组净值 1,210、逐日诊断 242 行。完整回归见本轮提交。没有重新下载或重跑研究；留存文件在 Git 忽略目录中，不入库。该工具仍无法检测协调重写复现包、身份和 CSV 的攻击，也不认证市场数据来源或研究公式。
