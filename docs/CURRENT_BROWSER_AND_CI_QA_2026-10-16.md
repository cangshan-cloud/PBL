# 当前版本浏览器回归与 Windows CI 排查（2026-10-16）

实际执行者：Codex。基线为已推送 `4067db9` 加本轮工作树修正；不是已发布提交或正式十分钟连续演示。Mac 使用临时 SQLite、内联 FastAPI `127.0.0.1:18000` 和 Vite `127.0.0.1:15173`，均在验收后停止。数据为仓库内置合成 `demo_daily` 0.2.0；没有触碰主 Compose 数据库或私有真实样本。浏览器证据存于本机 Git 忽略目录 `output/playwright/current-qa-2026-10-16/`，不会随 Git 推送。

## 浏览器实测

| 场景 | 观察 | 结论 |
| --- | --- | --- |
| 清空分组数并点击运行 | 页面实时提示“分组数量须为 2～10 的整数”；总览仍为 0 条任务 | 无效请求被拦截 |
| 无效分组的未运行指标说明 | 初次发现 `Q0 − Q1`；修正后显示破折号，单测同时覆盖 0 与 `NaN` | 本轮修复，不再伪造分组标签 |
| 运行 20 日动量 | Run `7f2ba0a6-0bc4-4d81-a2fa-c08b466772a5` 成功，1,980 个观测 | 隔离 inline 链路通过 |
| 运行 5 日反转 | Run `e73b4e58-0f6c-45c5-91de-b8ec36d2b010` 成功，2,280 个观测 | 隔离 inline 链路通过 |
| 任务中心切换两条 Run | 标题、参数、规则结论、执行日志与所选 Run 一致 | 常规切换通过；未人为延迟网络制造极端竞态 |
| 报告中心切换两份 HTML | 内嵌报告分别显示对应标题和完整 Run ID | 常规切换通过；未人为延迟网络制造极端竞态 |
| 应用浏览器控制台 | 错误 0、警告 0；开发模式仅有 React DevTools 信息 | 通过 |

本轮并未在真实 Celery、Windows 浏览器或正式十分钟连续讲解中重做上述流程。浏览器测试使用开发版前端；生产构建另行通过。队长本人产品实测仍待补。

## CI 排查与处理

公开 GitHub Actions API 显示 `03b67c9`、`9c0a3bd`、`7153490`、`4067db9` 的工作流均为失败；最近的 [`4067db9` 运行](https://github.com/cangshan-cloud/PBL/actions/runs/38867426662) 中 Ubuntu 全部成功，Windows 在“Run backend tests”失败，后续前端步骤未执行。更早 `38382a4` 开始失败，而它首次加入 `data/sample/daily_prices.csv` 原始字节 SHA-256 与固定值相等的测试。匿名访问作业日志需要登录，不能把具体失败断言说成已直接看到。

基于代码差异和 Windows Git 常见检出换行行为，最可能原因是 CSV 被转换为 CRLF，导致原始字节摘要不同。本轮新增 `.gitattributes`，将 `data/sample/*.csv` 固定为 `text eol=lf`；本机 `git check-attr` 与 `git ls-files --eol` 均显示 LF。这个诊断在新提交的 Windows CI 成功前仍属于**待验证推断**，若仍失败须取得实际日志或继续缩小测试范围，不应宣称已修复。

2026-10-17 复核：修正提交 `3c926d5` 的 [CI 运行 #39011360370](https://github.com/cangshan-cloud/PBL/actions/runs/39011360370) 中 Ubuntu 与 Windows 两个 Verify 作业均为 `completed/success`，Windows 已通过原先失败的后端测试并完成后续前端测试和构建。这个结果支持换行诊断，但匿名作业日志仍不可读，不能声称直接看到了先前失败断言；也不能把 CI 当作 Windows Docker/WSL2 部署验收。复核执行者：Codex。

## 本机回归

- `npm test --prefix frontend`：13 项通过。
- `npm run build --prefix frontend`：通过。
- `make test`：后端 191 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：六观测黄金验算通过。
- `git diff --check`：通过。

本轮只保存脱敏浏览器快照，不上传密码、临时数据库或私有样本。Windows 部署验收仍暂缓，GitHub 的 Windows 单元测试通过也不能替代它。
