# Mac 端到端验收记录

## 本次环境与结论

- 验收日期：2026-10-11；设备：macOS；运行方式：本地 FastAPI + Vite + SQLite 内联任务模式。
- 使用隔离的临时数据库与数据目录，不使用团队正式数据。
- 浏览器实测通过：研究员登录、演示数据选择、20 日动量任务提交、指标与曲线显示、任务日志与结构化结论、独立 HTML 报告预览及下载、管理员数据页面、只读账号页面权限。
- 本次任务结果：演示数据 20 只证券、2,400 行；20 日动量得到 1,980 个观测和 99 个 IC 截面。报告包含 IC／Rank IC 与毛／成本后净值曲线。
- 下载验证：浏览器下载事件完成并产生 `factor-report-<Run ID前8位>.html`。
- 2026-10-11 当次未完成：浏览器拒绝本地 CSV 文件上传授权，因此没有把“管理员导入并发布”记为通过；Docker 服务当时未运行；Windows 环境待后续实测。Docker 部分已在 2026-10-12 补验，见下节。

## 2026-10-12 OrbStack 补充验收

- 使用仓库 Compose 启动 Web、API、Worker、PostgreSQL、Redis；API 与数据库、Redis 健康，前端可访问，Worker `inspect ping` 返回 `pong`。
- `tools/verify_compose_stack.py` 以研究员身份使用已发布的 `demo_daily` 数据提交 20 日动量研究。任务 `e7a889c8-f178-469a-bf4c-bc687931b97c` 由 Celery Worker 日志确认接收和完成，API 状态 `success / 100%`，报告 HTML 与内嵌 SVG 图表可读取。
- 该补验仅覆盖演示数据的容器化异步闭环；管理员上传 CSV 的浏览器操作与 Windows + WSL2 仍待验收。部署命令和注意事项见 `docs/ORBSTACK_DEPLOYMENT.md`。

## 本机复现步骤

前提：已按 README 安装项目 Python 与前端依赖。打开两个终端，使用临时 SQLite 数据库，避免污染现有环境：

```bash
# 终端一：项目根目录
E2E_ROOT=$(mktemp -d /private/tmp/fbl-e2e.XXXXXX)
export DATABASE_URL="sqlite:///$E2E_ROOT/factorlab.db"
export DATA_ROOT="$E2E_ROOT/data"
export TASK_EXECUTION_MODE=inline
cd backend
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
# 终端二：项目根目录
cd frontend
npm run dev -- --host 127.0.0.1
```

在 `http://localhost:5173/` 验证：

1. 研究员登录，打开研究工作台，保留默认的演示数据、20 日动量、5 分组和 10 bps 成本，运行研究；确认结果为“计算完成”。
2. 打开任务中心，核对数据版本、参数、日志和研究结论；再打开报告中心，核对两张曲线，下载 HTML 并离线打开。
3. 退出后以管理员登录，确认数据集页面存在导入表单。若浏览器允许文件上传，可选 `data/golden/daily_prices.csv` 验证导入、质量检查和发布；本次未完成这一步。
4. 退出后以只读账号登录，确认没有导入表单，研究工作台的运行按钮禁用，任务和报告仍可查看。
5. 切换账号后重新打开研究工作台，确认即时指标为空，不显示前一个登录账号的未归档页面状态。

首次运行的演示账号见 README。共享环境须先更换默认密码和 JWT 密钥。验收结束后停止两个服务；临时目录可以保留供复核。

## 本次发现并修复

- 退出登录时前端未清空即时研究结果、报告预览等页面状态；已在退出流程中清理，并通过重新登录浏览器复测。
- SQLite 返回的 UTC 时间可能没有时区后缀，前端此前按本地时间解释，导致显示偏差；现在无后缀时间按 UTC 解析，浏览器显示为本地时间。

## 后续验收门槛

- 取得浏览器上传授权后，补做管理员 CSV 导入、质量预览、发布及新版本研究。
- 在 Windows + WSL2 环境重复 Compose、PostgreSQL、Redis、Celery Worker 的异步任务验收，并记录跨平台差异。
- 在 Windows + WSL2 环境重复核心演示，并记录启动时间、页面截图与差异。
