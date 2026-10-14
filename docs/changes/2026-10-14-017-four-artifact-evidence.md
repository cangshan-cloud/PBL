# CHG-20261014-017：历史任务四文件证据与报告摘要核对

- 日期：2026-10-14
- 类型：evidence integrity + acceptance tool
- 状态：implemented / verified on macOS OrbStack
- 关联提交：与本记录同次提交

## 背景与目标

上一轮独立工具已核对复现 JSON 的结果摘要及两份审计 CSV，但 HTML 报告没有纳入同一文件组；隔离 API/Worker 验收工具也只下载三份文件。需要可选地核对复现包中的 `report_sha256`，并让端到端验收默认保留报告证据。

## 决策过程

三文件离线 CLI 保持兼容，新增可选 `--report-html`；提供时按报告原始字节计算 SHA-256，与复现包的 `report_sha256` 比较。隔离写入式验收工具始终通过已有报告下载接口取得第四份文件并调用四文件校验。这样不新建后端接口、不重渲染旧报告，也不把普通摘要误称为签名。输出目录继续拒绝覆盖。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 可选报告文件摘要核对与 CLI 参数 | `tools/verify_historical_audit_exports.py::verify_exports`、`main` | 三文件兼容，四文件时额外核对报告 |
| 隔离任务验收下载 HTML 报告并调用四文件校验 | `tools/verify_historical_api_journey.py::run_journey` | 完整保留研究报告证据 |
| 正常、报告改动、缺摘要和四次下载回归 | `backend/tests/test_historical_audit_exports.py`、`backend/tests/test_historical_api_journey.py` | 防止报告错配被漏检 |
| 更新离线核对与 OrbStack 用法 | `docs/HS300_BUNDLE.md`、`docs/ORBSTACK_DEPLOYMENT.md` | 可供团队复测 |
| 登记变更 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `make test`：129 项通过。
- Mac OrbStack 独立项目 `factorlab-hs300-evidence-qa` 中，经 API/Redis/Celery 运行历史任务 `bcdffde2-5d5a-4d6d-a6be-1d926a262459`，四份 HTTP 附件下载并核对成功：4 因子、968 行逐日审计、32 条无标签信号，`report_verified=true`。离线 CLI 以 `--report-html` 对同组文件复验通过。
- 隔离项目的容器、网络和专用数据库卷已删除；下载证据留在 `/private/tmp/fbl-hs300-evidence-qa-downloads/`，不纳入 Git。原 `fbl` 五服务仍运行且健康，任务数仍为 26。

## 风险、回退与未决事项

结果及报告摘要只能发现意外错配；复现 JSON、CSV、HTML 和摘要如被协调重写，工具无法证明真实来源。它不验证私有行情源、因子公式或收益可交易性。Windows 环境未实测。
