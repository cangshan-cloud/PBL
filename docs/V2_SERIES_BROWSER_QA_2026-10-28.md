# 新 Celery Run 的浏览器序列 CSV 严格 V2 验收（2026-10-28）

## 范围与执行

实际执行者：Codex；队长及其他组员未人工签收。本轮使用 Playwright CLI 真实浏览器访问已预检的 `factorlab-historical-qa-20261025` 隔离 Web/API（`127.0.0.1:15122/18022`），只启 db、redis、api、web，不启 Worker、不创建新任务。以隔离研究员账号登录，从概览进入新 Celery 成功 Run `dc520031-3a62-40d7-ac1e-1fa3e9d1456f` 的任务中心详情；页面显示完整 Run 前缀、数据/因子/代码版本与完成日志。

依次实点“下载每日 IC CSV”“下载多空逐日 CSV”“下载各组逐日净值 CSV”“下载全量诊断 CSV”。四份浏览器下载仅留在 Git 忽略的 `output/playwright/v2-series-20261028/.playwright-cli/`；同 Run 的 V2 复现 JSON 使用前轮隔离 API 下载的 Git 忽略文件 `data/real/historical_api_v2_20261028/reproducibility.json`，没有把私有导出加入仓库。浏览器会话的 Playwright 页面快照和控制台日志也留在该忽略目录。

## 逐行核对结果

运行 `tools/verify_series_exports.py`，同时传入四份实际浏览器 CSV 和同 Run JSON，并使用 `--require-v2`。结果：`ic_rows=242`、`long_short_rows=242`、`group_nav_rows=1210`、`daily_coverage_rows=242`，退出码 0。工具检查 CSV 表头、完整 Run ID、原始数值、空值及日期/组顺序，严格核对 V2 整包摘要。四份文件 SHA-256：

| 浏览器文件 | SHA-256 |
| --- | --- |
| `ic-series-dc520031.csv` | `50f0361c2598d72be0160a40af3fd8fa2f9e1b62796defbf7962aee1ddf70ce0` |
| `long-short-dc520031.csv` | `a56da107c6eea180b4c9725cc6b838feb62919e38a37d8f5c70c2521cfdc5c52` |
| `group-nav-dc520031.csv` | `c89811dff9d1f3b4395d2e0ea466da8667e60fb39c17f60dff94df8fc1b038bf` |
| `daily-coverage-dc520031.csv` | `ef645f9527658728952934b9ce620faabad94c2bf12cd367de32b15a51a3968c` |

Playwright 控制台累计 3 条消息，其中 0 error、0 warning。随后关闭浏览器；仅对隔离项目执行 `docker compose down`，未带 `-v`，独立数据库卷与忽略的下载证据保留。收尾 `docker compose ls` 只显示主 `fbl` 五服务运行，主栈未操作。

## 证据边界

本轮补上[前轮严格 V2 离线记录](STRICT_V2_DOWNSTREAM_QA_2026-10-28.md)明确未覆盖的新 Run 浏览器序列 CSV 路径。它证明浏览器实际下载与同 Run 保存结果逐行一致，不是独立因子公式、行情来源/授权、策略可成交收益或队长本人产品验收。主网址仍未因本轮而升级 V2。
