# CHG-20261025-004 复现 JSON 歧义防线

## 问题与决策

Python 默认 JSON 解析接受重复键并保留最后一个值。不同工具可能对重复字段作不同解释，削弱导出证据的一致性。决定让普通复现、历史审计和历史复算共享同一严格读取及摘要核验入口：拒绝任意层级重复键，并仅接受整型格式版本 1。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_reproducibility_export.py::_unique_object`、`load_verified_export`、`verify_export`：严格读取并复用原结果/报告摘要检查。
- `tools/verify_historical_audit_exports.py::verify_exports` 与 `tools/verify_historical_recomputation.py::verify_recomputation`：复用严格入口，历史复算不再对文件二次解析。
- `backend/tests/test_reproducibility.py`、`backend/tests/test_historical_audit_exports.py`：重复键及布尔版本反例。
- `docs/REPRODUCIBILITY_EXPORT_CHECK.md`、`docs/HS300_BUNDLE.md`、索引与 A/B/C/D 四责任包：记录边界。

## 验证结果与未决事项

定向 13 项通过；本机私有包既存当前导出仍可严格复算，四因子、五分组、72,366 共同观测。全量测试和文档检查见本轮提交。OrbStack Docker socket 仍不可用，未做 Celery/HTTP 或浏览器重跑，也未操作主栈、原始私有数据或用户编辑的分工 Excel。校验仍不是防篡改签名、独立公式证明或数据来源授权证明。
