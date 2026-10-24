# CHG-20261023-004 完整证券子集异步执行与报告验收

## 问题与决策

CHG-20261023-003 证明容器 Web 对完整证券子集放行，但没有提交任务，不能推断 Worker 成功或报告可交付。本轮在同一独立 QA 数据卷实际提交一次完整子集 PE 调整价研究，并用受影响子集请求确认后端拒绝仍在创建前生效。只使用合成数据，不扩大到真实市场结论。实际执行者：Codex。

## 修改内容与位置

- `docs/MAC_SYMBOL_ADJ_GAP_WORKER_QA_2026-10-23.md`：记录隔离环境、任务 ID、参数、Worker 状态、报告摘要、拒绝结果和边界。
- `docs/CHANGE_INDEX.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` 及 A/B/C/D 四责任包：同步决策和验收状态。
- 隔离项目 `factorlab-browser-qa-1022-price` 的专用 PostgreSQL 卷：保留新增研究任务及报告；无仓库业务代码修改。

## 验证与边界

专用 Compose 预检 PASS；完整子集请求 201，Worker 任务成功并生成报告，交付 HTML 200 且归档 SHA 与可复现快照一致。受影响子集请求 400 后，任务/报告最终各 2。项目已 `down` 且保留卷，主栈未动。

本轮通过 API 而非浏览器提交；样本只有 2 股 4 日，`coverage=6` 且有 1 个零观测日，任何 IC/收益数值都不作为研究发现。未验证 Windows、真实市场来源及旧质量报告迁移。
