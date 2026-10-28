# CHG-20261028-005 下游离线核对统一提供严格 V2 闸门

## 问题与决策

虽然新 Celery 验收入口已要求 V2，下游审计 CSV、同源复算、每日序列和结果内部审计命令单独运行时仍默认兼容 V1。决定各自增加可选 `--require-v2`，让新版验收可在**同一命令**拒绝旧格式；默认保留 V1 读取，避免旧归档和教学材料被强制失效。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_historical_audit_exports.py::verify_exports`、`main`；`tools/verify_historical_recomputation.py::verify_recomputation`、`main`；`tools/verify_series_exports.py::verify_series_exports`、`main`；`tools/verify_research_result_consistency.py::verify_result_consistency`、`main`：将严格选项传给共同的复现包校验器。
- `tools/verify_historical_api_journey.py::run_journey`、`tools/run_isolated_historical_replay.py::run_isolated_replay`、`tools/verify_http_reproducibility.py::verify_http_run`：当前新任务/新下载路径向下游传递严格 V2。
- `backend/tests/test_downstream_v2_gate.py`、`test_series_exports.py`、`test_historical_api_journey.py`：四命令 V1 严格拒绝、V2 序列正例及入口参数透传。
- `docs/STRICT_V2_DOWNSTREAM_QA_2026-10-28.md`、`docs/SERIES_EXPORT_VERIFICATION.md`、`docs/HS300_BUNDLE.md`、`docs/REPRODUCIBILITY_EXPORT_CHECK.md`、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：用法、实测和边界。

## 验证与未决事项

四个下游核对器对 V1 严格拒绝的定向测试通过，V2 序列正例通过；留存新 Celery V2 Run 的审计 CSV、同源复算和保存结果内部审计在严格模式通过。后端全量 317 项及黄金研究样例通过。新 Run 的浏览器序列 CSV 未下载，故该真实文件路径仍待验。无应用 API、数据库或队列变更；主服务未改。无密钥摘要仍非数字签名。
