# 各组逐日净值 CSV 隔离浏览器验收（2026-10-26）

Mac OrbStack 专用项目 `factorlab-historical-qa-20261025` 通过预检后启动隔离 DB、Redis、API、Web，使用隔离研究员登录任务中心，选择旧成功 Run `f424f62b-4081-400c-89ef-79bbff4a4e59`。实际执行者：Codex；没有创建新任务，也未改主 `fbl` 栈。

浏览器实点“下载各组逐日净值 CSV”，保存 `group-nav-f424f62b.csv` 到忽略的 `.playwright-cli/`；SHA-256 为 `da03cc305ac9256557d6e07ffabe411c3faddc32dd0673eaf310a2ea3b6cf337`。文件 1,210 行、4 列，Q1–Q5 每组各 242 行，全部绑定完整 Run ID。`tools/verify_series_exports.py` 将其与隔离 API 上一轮只读下载的同 Run 复现 JSON 逐行比对，输出 `group_nav_rows=1210`；同时复核已有 IC、多空文件各 242 行。浏览器控制台 0 error、0 warning。随后关闭浏览器及隔离四服务，卷保留；私有 CSV 和复现包不入库。

本轮只核对**已保存的毛净值序列**，并非独立重算分组或真实撮合。研究工作台的新任务入口未实点，队长本人产品实测仍待完成。文件自带结果 SHA 不是外部签名，数据来源/许可和投资有效性未获新认证。
