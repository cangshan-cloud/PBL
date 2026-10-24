# Mac 隔离容器完整证券子集浏览器闭环（2026-10-23）

## 目标与环境

接续 [API/Worker 验收](MAC_SYMBOL_ADJ_GAP_WORKER_QA_2026-10-23.md)，补齐“浏览器实际点击运行”尚未验证的边界。使用专用 Compose 项目 `factorlab-browser-qa-1022-price` 与保留的数据卷；启动前预检通过，五服务就绪。主栈未动。

研究员在 Web 工作台选择已发布的 `symbol_adj_gap_qa_1023` 版本 `20261023.112628.122645`，价格口径 `close × adj_factor`、PE 单因子、2 组、证券 `000001.SZ,000003.SZ`、日期 2025-01-02 至 2025-01-07、单边成本 10 bps，点击“运行研究”。

## 浏览器观察

- 页面绑定新 Run `94cf90bd-f6a9-4bc5-8edd-dc14c191c969`，状态成功；有效观测 6、候选证券日 8、覆盖率 75%、零观测日 1。[研究页截图](../outputs/qa-2026-10-23/container-symbol-adj-complete-run-2026-10-23.png)
- 任务中心该 Run 成功，保存数据版本 ID `baaa0a6f-93ff-472f-b3dd-636818647d3f`、因子版本、代码版本及上述价格口径、证券和分组参数；日志显示排队、Worker 开始及后续执行事件。
- 报告中心新增同一 Run 的归档，在线预览注明 `close × adj_factor`。[报告页截图](../outputs/qa-2026-10-23/container-symbol-adj-complete-report-2026-10-23.png)
- 点击“下载披露版HTML”后浏览器下载 `factor-report-94cf90bd-disclosed.html`，文件 13,202 字节；保留[下载副本](../output/playwright/container-symbol-adj-complete-report-2026-10-23.html)，可检索到完整 Run ID、价格口径和“仅用于课程研究”限制语。

验收后关闭浏览器并对**专用项目**执行 `down`，未使用 `-v`，数据卷保留。此次未重复受影响证券的页面拦截（见[上一轮](MAC_SYMBOL_ADJ_GAP_BROWSER_QA_2026-10-23.md)），也不把 2 股 4 日合成样本的 IC/收益解释为因子有效性；Windows 和真实数据结论未验。
