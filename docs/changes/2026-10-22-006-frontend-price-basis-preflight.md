# CHG-20261022-006 研究页提交前复权口径提示

## 问题与决策

CHG-005 已让服务端在提交前拒绝重复复权，但页面仍允许用户选择并点击错误配置，之后才显示 HTTP 400。决定复用所选数据版本已有的 `quality_report.adapter_report.source_adjustment_flags`，在研究页即时提示并禁用运行按钮；服务端守卫不移除，避免前端状态过期或被绕过。历史模式不使用普通价格口径，不受该提示影响。实际执行者：Codex。

## 修改内容与位置

- `frontend/src/research-config.ts::validateResearchConfiguration`：输入增加可选来源状态；仅在普通研究选择 `factor_adjusted` 且适配来源标记为已复权或畸形时返回明确错误。`source_close`、标记 `3` 和无适配标记按原规则继续。
- `frontend/src/main.tsx` 的 `QualityReport`、`researchInput` 与研究页页首按钮：读取所选版本状态，显示统一验证错误，并在错误配置下禁用运行按钮；`runResearch` 仍保留提交前校验。
- `frontend/tests/research-config.test.ts`：覆盖单因子、多因子、1/2/3 标记、畸形状态、默认价格和历史模式。
- `docs/PRICE_BASIS.md`、总索引与 A/B/C/D 四责任包：同步交互规则和验证边界。

## 验证与边界

前端 **47 tests passed**，生产构建通过。本轮未部署 Web 或浏览器实点，不宣称已在运行页面验收；测试数据来源状态仍只代表 CSV 来源声明，不能自动证明真实复权口径。服务端对异常提交继续返回 400。
