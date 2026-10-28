# CHG-20261028-008 逐股观测到每日 IC 与汇总的独立验算

## 问题与决策

前轮已经独立检查三个完整交易日的源 CSV 到 Run 逐股观测；但全期 IC 主要依赖项目研究算法复算或同源结果一致性检查。决定增加标准库只读验算器，从新历史 Run 的逐股产物独立计算每日 Pearson IC、并列平均名次 Rank IC 和五项汇总，再与 V2 保存结果对照。明确两段证据的不同覆盖范围，不把 242 日 IC 验算写成全年源行情重算。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 独立每日 IC、Rank IC、汇总与产物摘要检查 | `tools/verify_independent_ic_from_observations.py::verify`、`_pearson`、`_ranks` | 避免复用应用研究算法 |
| 六观测手算正例及篡改、缺失、重复、摘要反例 | `backend/tests/test_independent_ic_from_observations.py` | 锁定数学及拒错行为 |
| 实际 Run 输出与证据边界 | `docs/INDEPENDENT_IC_RUN_AUDIT_2026-10-28.md` | 课程验收可追溯 |
| 总索引与四人责任包 | `docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 按团队约定同步 |

## 验证与未决事项

私有新 Celery Run 的 72,366 条观测、242 日 IC/Rank IC 及五项汇总全部通过，最大绝对差 `1.11e-16`。构造反例 3 项测试通过；后端全量、黄金核对、台账与链接检查随提交执行。该工具不读取原始行情，不验证所有因子值由源 CSV 正确生成，也不证明数据授权或投资效果。用户改动的分工 Excel 不处理。
