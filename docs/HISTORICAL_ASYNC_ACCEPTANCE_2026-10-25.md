# 历史私有包异步链路隔离验收（2026-10-25）

本记录只描述本机 Mac/OrbStack 软件链路，不包含私有行情字节。实际执行者：Codex；队长本人产品实测未发生。

## 隔离边界

- 主项目 `fbl` 五服务验收前后均运行；未对其数据库、Redis、镜像或数据卷执行写入、重建与清理。
- 专用项目 `factorlab-historical-qa-20261025` 使用独立网络、PostgreSQL 卷 `factorlab-historical-qa-20261025_postgres_data`、本机 API 端口 18022 和临时运行目录 `/private/tmp/factorlab-historical-qa-JYdB72`。
- `data/sample` 与 `data/real/bundles` 仅只读挂载；API/Worker 共同写入专用运行目录。私有 HTTP 导出保存在 Git 忽略的 `data/real/historical_api_qa_2026-10-25/` 及 `data/real/historical_api_qa_codified_2026-10-25/`，不提交仓库。

## 验收结果

首次临时配置漏挂 `/data/sample`，API 启动时因找不到内置演示 CSV 而退出；补上只读样本挂载后四服务健康。第一条任务 `2d9c22f2-6674-4972-a855-41b339294395` 成功。随后新增正式 `docker-compose.historical-qa.yml` 和预检脚本，用同一专用项目重建 API，并提交第二条任务 `189a7e0e-16f2-4a9f-894f-e4a167efaf96`；第二次也成功。

两条任务均使用私有封存包 `hs300_2024_0375298bd2c8ac52`，HTTP 下载复现 JSON、逐日审计 CSV、无标签 CSV 和 HTML 报告，核对 4 因子、968 行逐日审计、32 条无标签信号及报告摘要。第二条任务的复现 JSON 对本机同一私有包按当前源码严格复算通过：5 分组、72,366 个共同观测。第二条证据的文件 SHA-256：复现 JSON `32430784ef87df8a84da86a5103d38a268a33a914d1a8d73391d074387435f76`，HTML `ada1f50fce901e535ad226ab7bebd4c1b0941fbc8e48e83d5c47d06148c26178`。这些摘要只用于本机证据核对，不是来源认证或数字签名。

验收后只对精确隔离项目执行了不带 `-v` 的 `down`；隔离容器与网络已停止/移除，专用 PostgreSQL 卷仍存在，运行目录及私有导出未删除。再次核对时 `docker compose ls` 仅显示主 `fbl` 项目运行，主栈五服务仍在。

## 可重复执行

1. 在系统临时目录创建全新 `factorlab-historical-qa-*` 运行目录，并设置 `FACTORLAB_HISTORICAL_QA_RUNTIME_DIR` 为其绝对路径；准备本机 Git 忽略的封存包，不能把私有行情提交到仓库。
2. 运行 `python3 tools/verify_historical_qa_compose.py --project-name factorlab-historical-qa-<唯一后缀> --runtime-dir <目录>`。仅在预检通过后，以**完全相同**的项目名和环境变量执行 `docker compose -p <项目名> -f docker-compose.yml -f docker-compose.historical-qa.yml up --build -d db redis api worker`。
3. 设置隔离栈对应的 `FACTORLAB_HISTORICAL_ADMIN_PASSWORD` 和 `FACTORLAB_HISTORICAL_RESEARCHER_PASSWORD`，使用 `tools/verify_historical_api_journey.py --api-url http://127.0.0.1:18022/api/v1 --bundle-id hs300_2024_0375298bd2c8ac52 --output-dir <新的私有目录> --acknowledge-isolated-writes`。该命令会创建隔离数据库记录，绝不可指向主栈 8000 端口。
4. 用 `tools/verify_historical_recomputation.py <导出目录>/reproducibility.json data/real/bundles/<包ID>/manifest.json` 做同源当前源码复算。验收结束只对精确隔离项目执行 `docker compose ... down`，**不要加 `-v`**，保留证据及专用卷以便复查。

未覆盖：Windows、浏览器交互、多人并发、官方成分时点的外部独立核验、数据授权、独立因子公式审计及可成交投资收益。
