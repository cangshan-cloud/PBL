# CHG-20261025-003 历史审计导出格式版本门槛

## 问题与决策

历史审计 CSV 离线核对已验证结果摘要和行内容，但未校验复现包格式版本；缺失或未知版本可能被按当前结构解释。决定只接受整型 `schema_version=1`，拒绝布尔值（Python 中布尔值可与整数 1 相等）。这只约束导出解释，不证明行情或因子公式正确。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_historical_audit_exports.py::verify_exports`：在读取审计数据前检查顶层对象及格式版本。
- `backend/tests/test_historical_audit_exports.py::_write_bundle`、`test_unsupported_schema_is_rejected_before_audit_comparison`：正例采用正式版本；覆盖缺失、未知和布尔版本反例。
- `docs/HS300_BUNDLE.md`、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：更新验收口径和旧复算描述。

## 验证结果与未决事项

定向 6 项测试通过；全量回归和文档台账检查见本轮提交。OrbStack Docker socket 仍不可用，本轮没有隔离 Celery/HTTP 或浏览器验收，未改动主栈与任何数据卷。既存私有 `data/real/` 原始数据和用户编辑的分工 Excel 均未改动；队长本人产品实测、数据授权与独立公式核验仍待完成。
