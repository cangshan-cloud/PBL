# CHG-20261019-019 现有 OrbStack 栈浏览器端到端验收

## 问题与决策

CHG-20261019-018 更新了现有 `fbl` 的 API、Worker、Web 镜像，但只读健康检查不能证明新上传页面和研究报告闭环。决定在当前 Mac/OrbStack Compose 栈上进行一次明确命名的浏览器写入验收：三行合成 CSV 用于上传契约，原有 `demo_daily` 用于足量因子研究。合成样本不作为投资研究证据，保留数据版本及任务供队长复核，不删除既有记录。实际执行者：Codex。

## 修改内容与对应位置

- 无产品代码修改。浏览器实测路径：`frontend/src/main.tsx` 的数据集、研究工作台与报告中心；上传契约位于 `frontend/src/adapter-upload.ts`，后端适配/发布位于 `backend/app/main.py`、`backend/app/services/datasets.py`，研究运行位于 `backend/app/services/runs.py`。
- 新增本记录及 `docs/CHANGE_INDEX.md` 索引；在 `docs/ORBSTACK_DEPLOYMENT.md` 和 `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` 补充对应验收事实。
- 页面截图：`outputs/qa-2026-10-19/compose-dataset-published.jpg`、`outputs/qa-2026-10-19/compose-report-center.jpg`。浏览器下载的 HTML：`/Users/judai/Downloads/factor-report-56b06bd9.html`，不纳入仓库。

## 结果与证据

1. 更新后的主栈原有 2 个已发布数据版本。初次适配预览的原文件 SHA-256 为 `75100e7c7d06dbe27cc3e83955d48ddc3955fb569c9aa53b0d4906e7bae7120a`；将最后一行收盘价由 12 改成 13 后，页面清除旧预览，直接导入被“文件已更换，请重新预览后再适配导入”拦截，未形成草稿。
2. 重新预览显示新原文件 SHA-256 `7929852e418d5dc5a2d60ac657cc7e773f6a445bc2013e4760f2895a2bf8d58b`、3 行标准化数据及 1 个周末日期/2 行行情提醒。导入草稿后顶部提醒仍显示相同计数；`compose_accept_20261019` 的版本 `20261019.133241.102062` 发布成功，3 行、2 只证券。版本的标准化数据 SHA-256 为 `aec52b6454dcf9734f23c1a1fe87ec4fb7bb6b362e0094d31f7ecfe8f2117334`，不能与原文件指纹混同。发布后数据版本数为 3。
3. 选择原有 `demo_daily` 版本 `0.2.0`、20 日动量、20 日回看、5 组、10 bps 单边成本，研究 Run `56b06bd9-7d61-4b2b-aa17-19e1b7e101e6` 成功。页面显示有效观测 1980、IC 均值 0.2451、Rank IC 0.2259、成本后多空累计收益 53.78%。这些是演示数据上的软件验收数值，不代表真实市场可投资收益。
4. 报告中心自动出现本次报告并在线预览；点击“下载HTML”产生 38,249 字节文件，文件含完整 Run ID、1980、0.2451、53.78%；本机文件 SHA-256 为 `d70637a5839ecfe47b8764b959c980e7b9105130e3a89348a6d973125aeefe74`。

## 边界与后续

- 测试仅覆盖 Mac/OrbStack 主栈、单管理员、一个合成上传版本和一个演示研究任务；未覆盖 Windows、并发负载、真实交易所日历或生产安全。周末提示只做人工复核，不自动过滤记录。网页文件选择器在本次自动化中响应偏慢，未做可复现的应用性能测量，不能据此归因后端。
- 主栈保留新增验收数据版本、Run 和报告；没有重置数据库或清理原有成果。上传用临时本机 CSV 可在验收后移除，报告文件与仓库截图保留。
