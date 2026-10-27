# 普通研究任务复现包离线核对

从同一成功任务下载 JSON 复现包和 HTML 报告后，在项目目录执行：

```bash
python3 tools/verify_reproducibility_export.py /path/to/reproducibility.json --report-html /path/to/report.html --require-v2
```

如果只保存了 JSON，可省略 `--report-html`；这时不能验证报告文件字节。**按本轮代码重建服务后**的新导出为整型 `schema_version=2`：保留 `result_sha256`，另以 `bundle_sha256` 覆盖除该摘要自身以外的整个规范 JSON，包括 Run 身份、参数、数据版本、因子、报告摘要和日志。当前未重建的运行中服务可能仍导出 V1，须先查看文件版本。离线工具使用 Python 标准库、拒绝任意层级重复键，先重算结果摘要，再重算整包摘要；提供报告时另核对报告原始字节的 `report_sha256`。推荐对确认来自新版服务的下载使用 `--require-v2`，防止缺少整包摘要的 V1 文件被当作新版验收。

旧 `schema_version=1` 文件仍可不带该选项读取，只校验原有结果/可选报告摘要；旧文件没有整包身份绑定，也不会被回写。尚无结果的待运行任务复现包不作为研究结论验收，即使它本身是 V2，也会被本离线工具拒绝。

通过仅表示下载文件与复现包内摘要相符。摘要无密钥，攻击者若能同时重写内容和摘要仍可伪造；即使 V2 整包通过，也**不是数字签名**，不证明原始行情、因子计算、代码版本真实或未来收益。旧 V1 可兼容读取意味着不指定 `--require-v2` 时仍有版本降级空间。历史沪深 300 研究还需核对两份审计 CSV，应使用 [`HS300_BUNDLE.md`](HS300_BUNDLE.md) 中的历史四文件工具。设计与验证见 [CHG-20261027-012](changes/2026-10-27-012-bound-reproducibility-bundle.md)。
