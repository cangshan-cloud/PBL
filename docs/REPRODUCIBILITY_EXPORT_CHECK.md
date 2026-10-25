# 普通研究任务复现包离线核对

从同一成功任务下载 JSON 复现包和 HTML 报告后，在项目目录执行：

```bash
python3 tools/verify_reproducibility_export.py /path/to/reproducibility.json --report-html /path/to/report.html
```

如果只保存了 JSON，可省略 `--report-html`；这时仅核对 `result_sha256`。工具使用 Python 标准库，要求整型 `schema_version=1` 且任意层级不能有重复 JSON 键，按平台定义的规范 JSON 序列化重算结果摘要；提供报告时按报告原始字节重算 `report_sha256`。不接受尚无结果的待运行任务复现包。

通过仅表示下载文件与复现包内摘要相符。摘要无密钥，不是防篡改签名；工具不验证原始行情、因子计算、代码版本，也不证明未来收益。历史沪深 300 研究需要同时核对两份审计 CSV，应使用 [`HS300_BUNDLE.md`](HS300_BUNDLE.md) 中的历史四文件工具。
