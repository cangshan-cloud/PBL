# 多空逐日 CSV 隔离浏览器验收（2026-10-26）

本轮在 Mac OrbStack 的专用 Compose 项目 `factorlab-historical-qa-20261025`、Web `127.0.0.1:15122` 上执行；未替换主 `fbl` 五服务。运行目录为私有本机目录 `/private/tmp/factorlab-historical-qa-JYdB72`，导出文件仅留在忽略的 `.playwright-cli/` 目录，不随仓库发布。实际执行者：Codex，不代表队长或其他组员人工签收。

1. Compose 预检通过，启动隔离 DB、Redis、API、Web；以隔离研究员账号进入任务中心，打开旧成功 Run `f424f62b-4081-400c-89ef-79bbff4a4e59`。
2. 实点“下载多空逐日 CSV”，浏览器保存 `long-short-f424f62b.csv`。文件 SHA-256 为 `a3a5a3b7c9965add8193d84aabf99c213dbd276109521aa6a7130af6024fc164`。
3. 文件有 242 条数据行、9 列；全部行绑定上述完整 Run ID，单边成本参数均为 10 bps。140 个毛日收益为负，负号保留；逐行检查 `gross_return - cost = net_return`，误差阈值 `1e-9`，无失败行。
4. 浏览器控制台记录 0 error、0 warning。前端 75 项测试、生产构建、后端 283 项和黄金样例通过。

限制：本轮没有对下载 CSV 与复现 JSON 作独立逐值比对，未实点新任务研究工作台入口，也未验证金融可交易性。该文件是已保存分析结果的便携副本，收益与成本都是比例，不是百分数；包含固定简化成本，不模拟真实成交。
