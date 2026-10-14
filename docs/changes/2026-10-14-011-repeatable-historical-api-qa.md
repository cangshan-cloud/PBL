# CHG-20261014-011：可重复的历史包 API/Worker 验收工具

- 日期：2026-10-14
- 类型：tool + tests + evidence
- 状态：implemented / verified on macOS OrbStack
- 关联提交：与本记录同次提交

## 背景与目标

历史研究的隔离容器验收已成功，但注册、发布、排队、下载和核对依赖一次性临时脚本，团队成员无法按统一命令复测。需要把软件验收步骤固化，同时避免误写主 `fbl` 数据库。

## 决策过程

使用独立的宿主机 CLI 调用现有 HTTP API，并复用独立的审计导出核对器；不在后端新增“测试专用”路由，也不把私有行情打包进仓库。工具要求显式 API 地址、封存包 ID、全新证据目录、两个环境变量密码和 `--acknowledge-isolated-writes`；这是写入式验收，必须在独立 Compose 项目运行。现有包版本可复用，草稿可发布；任务仍新建，以便验证真正的 Worker 链路。输出目录拒绝覆盖。隔离端口用 Compose `!override`，防止基础文件的 8000 端口与主栈碰撞。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| HTTP 注册/发布、提交轮询、三文件下载与核对，写入确认和输出保护 | `tools/verify_historical_api_journey.py::ApiClient`、`run_journey`、`main` | 团队可重复执行真实容器验收 |
| 正常、复用、任务失败及缺少写入确认的回归测试 | `backend/tests/test_historical_api_journey.py` | 防止工具误覆盖证据或虚报成功 |
| 隔离 Compose 用法与安全清理、更新验收边界 | `docs/ORBSTACK_DEPLOYMENT.md`、`docs/HS300_BUNDLE.md` | 避免误用主库，并明确浏览器与容器证据 |
| 登记变更 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `make test`：120 项通过。
- 本机隔离项目 `factorlab-hs300-script-qa` 的 API 发布于 127.0.0.1:18000，独立数据库/Redis/运行目录；CLI 返回任务 `77451e63-e45c-4e76-8b08-d0067ed379f0` 成功，三文件核对为 4 因子、968 行逐日审计、32 条无标签信号。
- 首次 Compose override 端口列表叠加导致 8000 已占用；改为 `ports: !override` 后正常启动，故在部署文档中明确这一点。
- 隔离项目的容器、网络及专用 PostgreSQL 测试卷已删除；证据留在 `/private/tmp/fbl-hs300-script-qa-evidence/`，不纳入 Git。原 `fbl` 五服务仍运行、四个带健康检查的服务均 healthy，持久任务数仍为 26。

## 风险、回退与未决事项

此工具有意创建数据集/任务，命令行确认无法替代操作者核对 API 地址与 Compose 项目名；不要指向主栈。它证明下载与保存的审计内容一致，不证明真实行情、因子公式或可交易收益。只有 Mac/OrbStack 实测；Windows、多人并发和私有数据再分发未验收。
