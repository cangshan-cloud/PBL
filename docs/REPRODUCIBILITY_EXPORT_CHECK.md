# 普通研究任务复现包离线核对

从同一成功任务下载 JSON 复现包和 HTML 报告后，在项目目录执行：

```bash
python3 tools/verify_reproducibility_export.py /path/to/reproducibility.json --report-html /path/to/report.html --require-v2
```

如果只保存了 JSON，可省略 `--report-html`；这时不能验证报告文件字节。**按本轮代码重建服务后**的新导出为整型 `schema_version=2`：保留 `result_sha256`，另以 `bundle_sha256` 覆盖除该摘要自身以外的整个规范 JSON，包括 Run 身份、参数、数据版本、因子、报告摘要和日志。当前未重建的运行中服务可能仍导出 V1，须先查看文件版本。离线工具使用 Python 标准库、拒绝任意层级重复键，先重算结果摘要，再重算整包摘要；提供报告时另核对报告原始字节的 `report_sha256`。推荐对确认来自新版服务的下载使用 `--require-v2`，防止缺少整包摘要的 V1 文件被当作新版验收。

旧 `schema_version=1` 文件仍可不带该选项读取，只校验原有结果/可选报告摘要；旧文件没有整包身份绑定，也不会被回写。新 V2 的待执行、运行中、失败或取消任务若尚无结果，可核验整包摘要，命令输出为 `"result_verified": false`、`"bundle_verified": true`；这只说明快照文件完整，**不是研究结果通过验收**。成功任务缺结果、无结果却带结果或报告摘要均会拒绝。V1 的无结果包仍不作为有效离线导出。

通过仅表示下载文件与复现包内摘要相符。摘要无密钥，攻击者若能同时重写内容和摘要仍可伪造；即使 V2 整包通过，也**不是数字签名**，不证明原始行情、因子计算、代码版本真实或未来收益。旧 V1 可兼容读取意味着不指定 `--require-v2` 时仍有版本降级空间。历史沪深 300 研究还需核对两份审计 CSV，应使用 [`HS300_BUNDLE.md`](HS300_BUNDLE.md) 中的历史四文件工具。设计与验证见 [CHG-20261027-012](changes/2026-10-27-012-bound-reproducibility-bundle.md)。

2026-10-28 在隔离 OrbStack API 中，对既有成功历史 Run 实际下载 V2 JSON 与 HTML，严格 V2 整包、结果、报告摘要及保存结果内部审计均通过；只读证据见[隔离 HTTP 验收](V2_REPRO_HTTP_QA_2026-10-28.md)。该隔离栈已关闭；主 `fbl` 服务未在本轮重建，不能据此认定主网址已升级。

后续同类隔离 HTTP 验收可直接运行[只读检查工具](HTTP_REPRODUCIBILITY_TOOL_2026-10-28.md)：指定 loopback API 和已成功的 Run ID，密码从环境变量读取，严格检查 V2 与任务身份，可选结果内部审计；它不创建新任务或持久化下载文件。
