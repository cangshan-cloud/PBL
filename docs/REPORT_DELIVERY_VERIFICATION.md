# 报告披露版离线核对

## 输入与运行

从同一次任务分别保存四个文件：

1. `GET /api/v1/reports/{run_id}/download` 的原始 HTML（不使用披露版替代）。
2. `GET /api/v1/reports/{run_id}/delivery` 的披露版 HTML。
3. `GET /api/v1/datasets/{dataset_version_id}` 返回的数据版本 JSON 对象，保留 `id`、`dataset_key`、`version`、`checksum` 和完整 `quality_report`。
4. `GET /api/v1/reports` 中该 Run 对应的**单个对象**，单独存为 JSON；保留 `run_id`、`dataset_version_id`、`dataset_checksum_sha256`、`checksum`。不要把整个列表直接传给工具。

在项目根目录运行：

```bash
.venv/bin/python tools/verify_report_delivery.py archived.html disclosed.html dataset.json report-summary.json
```

退出码 0 和 `"verified": true` 表示：原始 HTML 字节的 SHA-256 与报告摘要一致；报告摘要与数据版本 ID/SHA 一致；披露版只在原 HTML 首个 `<main>` 后插入披露段，其他字节复原后与原归档完全一致；风险段落与独立保存的数据版本质量报告一致。摘要、身份、披露文本或其他报告内容被替换时返回非零退出码。

## 证据边界

这是一致性核对，不是数字签名。四个输入若同时被同一方协调篡改，工具无法证明它们来自平台；应从可信平台分别获取并妥善保存。工具也不能证明原始股票行情真实、数据使用权、财务披露时点、因子指标正确或未来收益。旧报告未含后续质量字段时只会核对当时可取得的元数据，不回填旧归档。合成演示数据仅证明软件流程。

自动正反例见 `backend/tests/test_report_delivery_verifier.py`。变更决策见 [CHG-20261021-002](changes/2026-10-21-002-offline-report-delivery-verifier.md)。

## 本机 API 一键只读核对

在 Mac + OrbStack 主栈可访问时，可对**已有**报告运行：

```bash
FACTORLAB_QA_PASSWORD='<本机账号密码>' .venv/bin/python tools/verify_live_report_delivery.py <唯一Run ID前缀>
```

不设置 `FACTORLAB_QA_PASSWORD` 时会隐式提示输入密码。命令只允许本机 HTTP API，先登录并确认前缀只匹配一份报告，再分别读取报告列表、数据版本、原归档和披露版；核对两份响应均为 HTML、披露响应头中的原归档 SHA 与报告摘要一致，然后在临时目录运行上述四文件核对。结束后临时文件被清理；终端仅输出 Run/数据身份、摘要、字节数和验证结果，不输出访问令牌或报告正文。它不会创建任务、修改报告或验证浏览器下载目录。

2026-10-21 对既有 BaoStock 报告 `170ef350-457b-4684-a2c8-7dab5f6275cf` 实测：原归档 24,387 字节、披露版 24,941 字节，归档 SHA-256 为 `be27976793a42becd9c63ac7f069665947dc7fb700cb4a63c8b7257e62801d33`，`verified=true`、`http_checked=true`，风险段落 1 个。此结果证明本机 API 返回的字节在当时一致，不证明浏览器文件已落盘，也不证明行情真实或授权。见 [CHG-20261021-006](changes/2026-10-21-006-live-report-delivery-audit.md)。

若已从浏览器下载，可增加 `--browser-file /绝对路径/文件.html`。命令会将该文件与同次 API 披露版响应**逐字节比较**，相同才输出 `browser_file_verified=true`；不读取其他下载文件，也不修改该文件。2026-10-21 应用内浏览器对上述 Run 的实际下载文件完成此核对：披露版 SHA-256 为 `041543222d86cc8bb36e6e5eae3714e882b541310a2f0fed00052552c1c8be8d`，24,941 字节完全一致。详见 [CHG-20261021-007](changes/2026-10-21-007-browser-report-download-byte-qa.md)。
