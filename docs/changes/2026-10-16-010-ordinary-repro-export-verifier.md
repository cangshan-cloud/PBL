# CHG-20261016-010：普通任务复现导出离线核对

- 日期：2026-10-16
- 类型：independent export verification + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

历史研究已有复现包、两份审计 CSV 和报告的离线核对工具；普通单因子任务虽然导出结果与报告摘要，却没有无需启动平台的校验入口。决定新增标准库 CLI，仅重算复现包 `result_sha256`，可选核对下载报告的原始字节摘要。待运行任务没有结果摘要，工具明确拒绝。它验证文件内部一致性，不冒充独立因子复算、数据来源认证或签名。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 普通复现包独立核对 CLI | `tools/verify_reproducibility_export.py::verify_export`、`main` | 无需 API 或第三方依赖即可核对摘要 |
| 真实后端导出与损坏夹具回归 | `backend/tests/test_reproducibility.py` | 覆盖正常结果、结果被改、报告被改 |
| 使用和边界说明 | `docs/REPRODUCIBILITY_EXPORT_CHECK.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` | 导师验收可按命令复测 |
| 总索引 | `docs/CHANGE_INDEX.md` | 记录本次决策 |

## 验证与结果

- 专项测试：3 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：182 项通过；其中隔离写入确认的负面用例预期打印命令行错误，测试进程退出码为 0。
- `.venv/bin/python tools/verify_reproducibility_export.py --help`：CLI 参数检查通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

摘要可以连同 JSON 一起被重写，不能证明作者身份；原始行情文件和运行代码也不在 JSON 内。HTML 报告必须作为同一任务的独立下载文件传入才会核对。Windows 本地 CLI 未验。
