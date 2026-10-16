# C 因子研究与指标验证

## 基本信息

- 负责人：待填写
- 学号：待填写
- 验收日期：待填写
- 对应责任占比：25%

## 交付清单

- [ ] 六个内置因子定义
- [ ] 预处理公式说明
- [ ] IC和Rank IC验算
- [ ] 分组收益和多空收益验算
- [ ] 换手率验算
- [ ] 平台结果差异记录
- [ ] 研究报告正文和风险说明

## 验收记录

填写样本数据、计算公式、独立结果、平台结果、允许误差、差异原因和复核人。

可使用 [`../GOLDEN_RESEARCH_VERIFICATION.md`](../GOLDEN_RESEARCH_VERIFICATION.md) 与 `python tools/verify_golden_research.py` 作为固定输入和平台输出。脚本通过证明代码与固定期望一致，不等于负责人本人做过手算。

真实历史包的局部公式与停牌标签抽样材料见 [`../INDEPENDENT_HS300_SPOTCHECK.md`](../INDEPENDENT_HS300_SPOTCHECK.md)。该材料由项目开发阶段准备，本轮未重新执行；不能直接据此勾选本人验收。

## 历史预填证据（2026-10-16，开发者整理）

- 六因子的字段依赖和定义见 [`../SINGLE_FACTOR_ANALYSIS.md`](../SINGLE_FACTOR_ANALYSIS.md) 与 `backend/app/domain/factors.py`；等权组合和预处理见 [`../MULTI_FACTOR_ANALYSIS.md`](../MULTI_FACTOR_ANALYSIS.md)。总市值因子在缺少 `total_mv` 的真实样本不能运行，市盈率数据仍需核对披露时点。
- 固定黄金样例脚本 `python3 tools/verify_golden_research.py` 在本机通过：6 个观测，覆盖 IC/Rank IC、分组收益、毛／净多空收益、成本及不等日期组均值；这是脚本证据，**不是 C 的独立手算**。
- 本次合成演示任务 `3b0d0a4c-c38c-410b-81bd-7d159047881d` 显示 1,980 个有效观测、IC 均值 0.2451、Rank IC 0.2259、ICIR 1.4267、99 个有效截面、毛／成本后多空累计收益 58.83%／53.78%。这些是软件输出，不是投资有效性证明；详见 [`../DEV_REHEARSAL_2026-10-16.md`](../DEV_REHEARSAL_2026-10-16.md)。

若课程要求一名成员现场独立手算，仍应保留实际执行者的“平台值／独立值／差异／容差”记录；当前不要求 C 个人签收，不把开发者脚本伪称为 C 的手算。

## 2026-10-16 异步链路本轮验收（开发者代执行）

- 执行者：Codex。当前 API/Worker 源码生成的 20 日动量任务有 99 个有效 IC 日、10 个分箱计数之和为 99、五组净值各 99 点；结果与 HTML 报告、复现包摘要一致。
- `tools/verify_golden_research.py` 固定六观测黄金样例通过；后端全量 185 项通过。详见 [`../ASYNC_ACCEPTANCE_2026-10-16.md`](../ASYNC_ACCEPTANCE_2026-10-16.md)。
- 本责任包结论：软件指标口径与固定黄金期望通过；本轮未独立重算真实市场全样本，也不宣称因子投资有效性。

## 2026-10-16 当前 Web→Celery 浏览器验收（开发者代执行）

同一 Run `4c05d255-32b8-4e92-b89d-8647e3953448` 在工作台、任务中心与 HTML 报告显示 99 个有效 IC 截面及一致的核心指标；JSON 与报告 SHA-256 离线核对通过。黄金样例脚本、后端 185 项测试再次通过。详见 [`../FULL_STACK_BROWSER_ACCEPTANCE_2026-10-16.md`](../FULL_STACK_BROWSER_ACCEPTANCE_2026-10-16.md)。不据此宣称真实市场或样本外收益有效；实际执行者：Codex。

