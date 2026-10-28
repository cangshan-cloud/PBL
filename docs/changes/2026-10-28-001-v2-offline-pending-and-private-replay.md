# CHG-20261028-001 V2 待执行包语义与私有历史离线复算

## 问题与决策

平台可导出待执行任务的 V2 复现快照，但离线工具原先把无结果一律判为损坏；同时新版私有历史包尚缺严格 V2 实测。决定对 V2 无结果快照只核对整包完整性并显式返回 `result_verified=false`，绝不把它当作研究结论；成功任务缺结果、无结果却带结果/报告摘要仍拒绝。旧 V1 无结果行为保持拒绝。隔离历史复算脚本内部改用严格 V2 验证，防止意外降级。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_reproducibility_export.py::load_verified_export`、`verify_export`：辨别 V2 未完成/失败快照与成功结果，仍验证整包摘要；返回结果验证布尔值。
- `tools/run_isolated_historical_replay.py::run_isolated_replay`：新生成历史任务的落盘校验强制 V2。
- `backend/tests/test_reproducibility.py::test_pending_bundle_has_no_result_and_respects_owner`：待执行包正例，伪成功状态及多余摘要反例。
- `docs/REPRODUCIBILITY_EXPORT_CHECK.md`、`docs/V2_REPRO_PRIVATE_REPLAY_2026-10-28.md`、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：口径、证据、限制和索引。

## 验证与未决事项

本机私有沪深 300 包经内存 SQLite 生成 Run，严格 V2 的 JSON/HTML 摘要与当前源码复算通过；242 个交易日、72,366 条有效观察的保存结果内部审计通过。后端 309 项、前端 86 项、前端构建和手算黄金样例均通过；变更索引及文档链接检查通过。OrbStack Docker socket 不存在，未做隔离 HTTP V2 下载或主栈升级；该待办保持开放。整包无密钥哈希不是签名；无结果包通过只代表文件自洽。
