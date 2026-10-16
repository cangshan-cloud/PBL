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

可使用 [`../GOLDEN_RESEARCH_VERIFICATION.md`](../GOLDEN_RESEARCH_VERIFICATION.md) 与 `python tools/verify_golden_research.py` 作为固定输入和平台输出。负责人仍需自行复核算式、记录运行环境与实际结果，并填写差异分析；脚本通过不等于个人验收材料已完成。

真实历史包的局部公式与停牌标签抽样材料见 [`../INDEPENDENT_HS300_SPOTCHECK.md`](../INDEPENDENT_HS300_SPOTCHECK.md)。该材料由项目开发阶段准备，负责人须亲自重做并在上方清单中记录实际证据，不能直接据此勾选个人验收。

## 可供 C 本人核对的预填证据（2026-10-16，开发者整理，未签收）

- 六因子的字段依赖和定义见 [`../SINGLE_FACTOR_ANALYSIS.md`](../SINGLE_FACTOR_ANALYSIS.md) 与 `backend/app/domain/factors.py`；等权组合和预处理见 [`../MULTI_FACTOR_ANALYSIS.md`](../MULTI_FACTOR_ANALYSIS.md)。总市值因子在缺少 `total_mv` 的真实样本不能运行，市盈率数据仍需核对披露时点。
- 固定黄金样例脚本 `python3 tools/verify_golden_research.py` 在本机通过：6 个观测，覆盖 IC/Rank IC、分组收益、毛／净多空收益、成本及不等日期组均值；这是脚本证据，**不是 C 的独立手算**。
- 本次合成演示任务 `3b0d0a4c-c38c-410b-81bd-7d159047881d` 显示 1,980 个有效观测、IC 均值 0.2451、Rank IC 0.2259、ICIR 1.4267、99 个有效截面、毛／成本后多空累计收益 58.83%／53.78%。这些是软件输出，不是投资有效性证明；详见 [`../DEV_REHEARSAL_2026-10-16.md`](../DEV_REHEARSAL_2026-10-16.md)。

C 必须独立列出至少一日的输入值、排序、手算 IC/Rank IC、分组收益、换手与成本，填入“平台值／独立值／差异／容差”表，并核对报告风险文字。本人自验结论：【待 C 填写】；计算文件及差异记录：【待填写】；C 签名／日期：【待填写】；交叉复核人及日期：【待填写】。

