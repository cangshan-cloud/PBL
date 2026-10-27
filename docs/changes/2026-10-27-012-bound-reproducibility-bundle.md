# CHG-20261027-012 新复现包整包摘要绑定身份

## 问题与决策

V1 的 `result_sha256` 只覆盖结果对象；Run ID、任务参数、数据版本及因子元信息即使被单独改动，结果摘要仍可通过。决定新导出改为 V2，保留结果摘要，同时增加对除 `bundle_sha256` 自身外整个规范 JSON 的 SHA-256。离线校验兼容旧 V1，但对新文件提供显式 `--require-v2` 防降级选项。摘要没有密钥，仍不是签名；本轮只增强意外漂移检测，不宣称抵抗有能力同时重算摘要的攻击者。实际执行者：Codex。

## 修改内容与对应位置

- `backend/app/services/reproducibility.py::build_reproducibility_bundle`：新包设 `schema_version=2`，规范编码所有元信息后计算 `bundle_sha256`；待执行包也包含整包摘要，但无研究结果仍不可用于结果验收。
- `tools/verify_reproducibility_export.py::load_verified_export`、`verify_export`、`main`：V1 兼容；V2 必须校验整包摘要；`--require-v2` 严格拒绝旧版。
- `tools/verify_compose_stack.py::verify_snapshot`：Compose 验收对新 V2 同步检查整包摘要，保留 V1 旧样例兼容。
- `backend/tests/test_reproducibility.py`、`test_historical_audit_exports.py`、`test_compose_stack_verify.py`：新包正例、Run/数据/因子/报告元信息篡改、缺摘要、严格 V2、V1 兼容和未知版本反例。
- `docs/REPRODUCIBILITY_EXPORT_CHECK.md`、`docs/SERIES_EXPORT_VERIFICATION.md`、`docs/HS300_BUNDLE.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：新版用法、旧证据范围与无签名限制。

## 验证与未决事项

本机内存任务的 API 下载 V2 包通过结果和整包摘要核对；元信息单独改动的反例失败，留存历史 V1 文件继续通过兼容读取。完整回归见本轮提交。尚未在隔离 OrbStack 浏览器重新下载 V2，也未将历史 V1 文件升级或回写。若用户不能信任下载来源，仍需独立签名或可信服务端记录；整包 SHA-256 不能提供真实性。
