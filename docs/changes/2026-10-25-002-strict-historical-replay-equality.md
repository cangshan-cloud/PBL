# CHG-20261025-002 历史结果复算严格逐值一致

## 问题与决策

历史结果离线复算原对浮点值使用相对/绝对容差。对于相同封存数据与当前源码的确定性复算，这允许导出者篡改极小数值并重新计算导出摘要后仍被判为通过。决定要求同类型、同结构、逐值精确相等；这是一项当前源码复现证据检查，不是独立公式证明。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_historical_recomputation.py::_same_result`：去掉浮点近似比较，保留结构递归及类型检查。
- `backend/tests/test_historical_recomputation.py::HistoricalRecomputationTests.test_recomputes_and_detects_self_consistent_result_change`：把 `ic_mean` 微小改动且自摘要重新计算的用例改为必须拒绝。
- `docs/HISTORICAL_CURRENT_REPLAY_2026-10-25.md`、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：记录边界与结果。

## 验证结果与未决事项

定向 2 项测试通过；本机既存私有封存包当前导出仍严格复算通过，四因子、五分组、72,366 个共同观测。全量测试和台账核对见本轮提交记录。OrbStack Docker socket 在本轮不可用，因此未执行计划中的隔离 Celery/HTTP 重跑；未触碰主栈或既有卷。仍不证明独立计算公式、真实可交易收益、行情授权及队长本人产品验收。用户修改的分工 Excel 未处理。
