# 研究配置与结果归属前端回归（2026-10-16）

## 目标与边界

上轮隔离浏览器已证明修改因子或分组时旧结果会隐藏，但该行为此前不在持续集成的自动测试里。本轮把“实际 API 参数”“配置键”“结果可见性”放进同一纯函数模块，并加入无需浏览器或私有数据的 Node 22 测试。它检查参数判定，不替代浏览器交互、后端指标、Celery 队列或最终课程演示。

## 实现与测试位置

| 内容 | 位置 |
| --- | --- |
| 单因子／等权多因子／历史模式参数、配置键、结果可见性、分组标签 | `frontend/src/research-config.ts` |
| 工作台调用同一构造结果提交 API 并决定旧结果是否显示 | `frontend/src/main.tsx` |
| 七项 Node 测试 | `frontend/tests/research-config.test.ts` |
| 本机及 CI 入口 | `frontend/package.json` 的 `npm test`、`.github/workflows/ci.yml` 的前端测试步骤 |

测试覆盖：提交参数与配置键完全对应；因子、数据版本、样本日期／证券、回看窗口、分组、价格口径、去极值、标准化和成本变化会隐藏旧结果；符号分隔符归一后不会无故隐藏；历史模式不受其隐藏的普通参数影响；切换模式和多因子成分会改变键；无窗口因子省略 `lookback`；缺数据／因子时拒绝构造任务；分组标签按 3 组或 5 组变化。

## 本机核对

- 实际执行者：Codex；Mac 工作树，基线提交 `9544edb` 加本轮改动。
- `npm test --prefix frontend`：7 项通过。
- `npm run build --prefix frontend`：TypeScript 与 Vite 构建通过。
- `make test`：后端 191 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：固定六观测验算通过。
- Windows/Ubuntu CI 工作流已加入测试步骤；只有该提交的远端作业完成并核对后，才能称其在两平台通过。前轮真实浏览器行为证据见 [`RESULT_PROVENANCE_BROWSER_QA_2026-10-16.md`](RESULT_PROVENANCE_BROWSER_QA_2026-10-16.md)，本轮未重跑浏览器或五服务栈。

## 后续

最终演示版本仍须核对本提交 CI、固定演示数据预检、真实五服务浏览器链路和队长十分钟连续讲解。若以后增加新研究参数，必须同时更新纯函数输入、请求参数、结果键测试和演示记录，避免旧结果误绑定。
