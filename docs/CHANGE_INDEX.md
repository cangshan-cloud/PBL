# 项目变更与决策总索引

本索引是项目修改记录的唯一入口。从基线提交 `5d081b4` 起，每次修改项目代码、测试、配置或正式文档，都应在同一次提交中增加或更新一条 `docs/changes/` 记录，并在下表登记。记录必须同时说明**做了什么、对应位置、为何选择、验证结果和未决事项**；仅有提交说明或聊天记录不算完成。目录模板见 [`changes/TEMPLATE.md`](changes/TEMPLATE.md)。

“对应位置”使用仓库相对路径和函数／类／章节名称，必要时增加行号；行号可能随以后修改变化，路径与名称应可长期定位。纯文档改动也应写明文档章节，并标注“无代码改动”。做扩展项决策但暂不写代码时，记录为 `decision-only`；尚待用户选择的方案只能标注 `open`，不得写作已决定。

| ID | 日期 | 类型／状态 | 内容 | 记录 | 对应位置 |
| --- | --- | --- | --- | --- | --- |
| CHG-20261012-001 | 2026-10-12 | governance / implemented | 建立变更、决策记录与总索引；扩展讨论保持未决 | [记录](changes/2026-10-12-001-change-governance.md) | `docs/CHANGE_INDEX.md`、`docs/changes/TEMPLATE.md`、`README.md` |
| DEC-20261012-001 | 2026-10-12 | decision-only / accepted | 扩展范围第一轮五项决定已获队长确认；具体扩展方案待后续轮次 | [记录](changes/2026-10-12-002-extension-frontier.md) | `docs/EXTENSION_OPTIONS.md`、`docs/PRD.md`、`docs/REAL_A_SHARE_SAMPLE.md`（只读依据） |
| DEC-20261012-002 | 2026-10-12 | decision-only / accepted | 真实数据私域使用、三道时间闸门、研究主张证据标准 | [记录](changes/2026-10-12-003-extension-choice.md) | `tools/fetch_real_a_share_sample.py`、`backend/app/services/runs.py`（只读依据） |
| DEC-20261012-003 | 2026-10-12 | decision-only / accepted | 唯一大扩展选择历史股票池与停牌/ST 可交易性口径 | [记录](changes/2026-10-12-004-extension-priority.md) | `docs/EXTENSION_OPTIONS.md`、`docs/REAL_A_SHARE_SAMPLE.md`（只读依据） |
| DEC-20261012-004 | 2026-10-12 | decision-only / accepted | 扩展与既有演示隔离，四人各自提交署名验收证据 | [记录](changes/2026-10-12-005-extension-integration.md) | `docs/TEAM_PLAN.md`、`backend/app/services/runs.py`（只读依据） |
| DEC-20261012-005 | 2026-10-12 | decision-only / accepted | 历史股票池首个范围确定为沪深 300 | [记录](changes/2026-10-12-006-universe-choice.md) | `tools/fetch_real_a_share_sample.py`、`docs/REAL_A_SHARE_SAMPLE.md`（只读依据） |
| DEC-20261012-006 | 2026-10-12 | decision-only / accepted | 2024 全年、按时点成分、价格和换手率因子边界 | [记录](changes/2026-10-12-007-universe-boundaries.md) | `backend/app/services/runs.py`、`backend/app/domain/factors.py`（只读依据） |
| DEC-20261012-007 | 2026-10-12 | decision-only / accepted | 可交易性表述、逐日排除审计、t/t+1 与缺失状态原则 | [记录](changes/2026-10-12-008-tradability-claims.md) | `backend/app/services/reports.py`、`backend/app/services/reproducibility.py`（只读依据） |
| DEC-20261012-008 | 2026-10-12 | decision-only / accepted | 连续日历窗口、次日 ST/零量和指数换出后的收益口径 | [记录](changes/2026-10-12-009-lookback-and-exits.md) | `backend/app/domain/factors.py`、`backend/app/domain/research.py`（只读依据） |
| DEC-20261012-009 | 2026-10-12 | decision-only / accepted | 历史模式参数范围、不可变数据包与年末标签 | [记录](changes/2026-10-12-010-parameter-bundle-yearend.md) | `backend/app/domain/factors.py`、`backend/app/models.py`、`backend/app/services/datasets.py`（只读依据） |
| DEC-20261012-010 | 2026-10-12 | decision-only / accepted | 年初预热、成分生效核验与收益聚合样本口径 | [记录](changes/2026-10-12-011-warmup-provenance-aggregation.md) | `backend/app/domain/factors.py`、`backend/app/domain/research.py`、`backend/app/services/reports.py`（只读依据） |
| DEC-20261012-011 | 2026-10-12 | decision-only / accepted | 历史股票池扩展的整体范围获最终确认 | [记录](changes/2026-10-12-012-expansion-shared-understanding.md) | `backend/app/domain/`、`backend/app/services/`、数据采集脚本与测试（拟涉及，无代码改动） |
| CHG-20261012-002 | 2026-10-12 | implementation / partial | 新增历史沪深 300 数据探针，真实两交易日验证通过 | [记录](changes/2026-10-12-013-hs300-feasibility-probe.md) | `tools/probe_hs300_history.py`、`backend/tests/test_hs300_probe.py`、`docs/HS300_DATA_FEASIBILITY.md` |
| CHG-20261012-003 | 2026-10-12 | evidence-only / partial | 年初年末历史成员端点有 28 出/28 入 | [记录](changes/2026-10-12-014-hs300-endpoint-check.md) | `docs/HS300_DATA_FEASIBILITY.md`（无代码改动） |
| CHG-20261013-001 | 2026-10-13 | implementation + evidence / partial | 全年历史成员采集与 12 月官方调整边界核验 | [记录](changes/2026-10-13-001-full-year-hs300-members.md) | `tools/fetch_hs300_members.py`、`tools/verify_hs300_members.py`、`tools/verify_hs300_official_2024.py`、`backend/tests/test_hs300_probe.py` |
| CHG-20261013-002 | 2026-10-13 | implementation + evidence / partial | 历史成员对应价格与交易/ST 原始数据采集及复验完成；完整包待建 | [记录](changes/2026-10-13-002-hs300-price-status.md) | `tools/fetch_hs300_prices.py`、`tools/verify_hs300_prices.py`、`backend/tests/test_hs300_prices.py`、`docs/HS300_PRICE_STATUS.md` |
| CHG-20261013-003 | 2026-10-13 | implementation + evidence / partial | 历史沪深 300 离线不可变包封存与复验 | [记录](changes/2026-10-13-003-hs300-offline-bundle.md) | `tools/build_hs300_bundle.py`、`tools/verify_hs300_bundle.py`、`backend/tests/test_hs300_bundle.py`、`docs/HS300_BUNDLE.md` |
| CHG-20261013-004 | 2026-10-13 | implementation / partial | 历史包平台注册、整包完整性核验与旧任务隔离 | [记录](changes/2026-10-13-004-hs300-platform-registration.md) | `backend/app/services/historical_bundle.py`、`backend/app/services/datasets.py`、`backend/app/services/runs.py`、`backend/app/main.py`、`backend/app/schemas.py`、`backend/tests/test_historical_bundle_registration.py`、`docs/HS300_BUNDLE.md` |

## 历史基线

`5d081b4` 及之前的提交属于本制度建立前的历史；原有 PRD、进度、真实数据验收和扩展建议分别见 [`PRD.md`](PRD.md)、[`PROJECT_STATUS_2026-10-12.md`](PROJECT_STATUS_2026-10-12.md)、[`REAL_A_SHARE_SAMPLE.md`](REAL_A_SHARE_SAMPLE.md)、[`EXTENSION_OPTIONS.md`](EXTENSION_OPTIONS.md)。这些文档和 Git 历史可供追溯，但不冒充逐次决策记录。若以后补录历史，必须明确标为“追溯补录”并说明证据来源。
