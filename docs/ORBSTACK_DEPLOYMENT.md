# macOS + OrbStack 部署

本项目使用标准 Docker Compose；OrbStack 提供 Docker 引擎和 `orbstack` context，不需要专用 Compose 文件。首次拉取 `postgres:16-alpine`、`redis:7-alpine`、`python:3.12-slim`、`node:22-alpine`，后两个基础镜像用于构建 API、Worker 和前端。

API 与 Worker 镜像从同一份 `backend/pyproject.toml` 读取依赖，先安装依赖再复制应用代码。2026-10-12 的重复构建中，两者的依赖安装层均显示 `CACHED`；若依赖清单或基础镜像变化，仍会重新安装。

## 启动

在项目根目录执行：

```bash
orb start
docker context show          # 应为 orbstack
docker info --format '{{.OperatingSystem}}'
docker compose config --quiet
python3 tools/verify_compose_config.py
docker compose up --build -d
docker compose ps
```

`docker compose ps` 中数据库、Redis、API 和 Worker 应显示 `healthy`；Worker 健康检查会向当前容器对应的 Celery 节点发送定向 `ping`，不是只检查进程存在。前端应显示 `Up`。

容器健康只证明容器内部检查通过，仍须从宿主机实际访问前端和 API。2026-10-14 一次排查中，已有 `fbl` 容器保持健康、API 容器内 `/health` 返回 200 且 8000 端口映射存在，但 Mac 宿主机的 8000 和 5173 端口均连接拒绝，`lsof` 没有对应 OrbStack 监听。`orbctl doctor` 检查通过，根因仍未定位。只对 `api`、`web` 执行 `docker compose restart api` 与 `docker compose restart web` 后，两个宿主机监听和 HTTP 页面均恢复；db、redis、worker 未重启，原有数据卷未删除。**这只是本次恢复事实，不保证能修复其他原因的端口故障。**正式演示前应把宿主机端口访问列为独立门槛；若失败，先收集 `docker compose ps`、宿主机 `curl`、容器内 `/health` 和 OrbStack 状态，再决定是否定向重启，不要直接删卷或全局重启。

浏览器打开 `http://localhost:5173/`，API 健康检查位于 `http://localhost:8000/health`。Compose 将这两个端口绑定到 Mac 的 `127.0.0.1`；PostgreSQL 和 Redis 不对宿主机发布端口。API 健康后前端与 Worker 才启动。数据库使用命名卷 `fbl_postgres_data`，导入的数据与报告写到仓库 `data/runtime/`，由 API 和 Worker 共享。

2026-10-14 浏览器复测后，API 默认 CORS 也允许 `http://127.0.0.1:5173` 前端来源：在现有 `fbl` 栈只重建并替换 API/Web，未重建 db、redis、worker 或数据卷；从 `127.0.0.1:5173` 以只读账号登录成功，`/favicon.svg` 返回 200，浏览器控制台无错误。若自定义 `CORS_ORIGINS`，须显式包含实际使用的前端来源；默认值不再自动追加。页面性能抽样及局限见 [`PAGE_QUERY_PERFORMANCE.md`](PAGE_QUERY_PERFORMANCE.md)。

本机演示可以使用 README 中的预置账号。仓库当前默认密码和 JWT 密钥仅适用于本机课程演示；若在共享环境运行，先根据 `.env.example` 创建 `.env` 并替换密钥与账号密码。Compose 统一从 `POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD` 生成 API/Worker 的数据库连接；密码目前需使用 URL 安全字符（字母、数字、`-`、`_`、`.`、`~`），因为它会直接拼入连接 URL。**已有数据库卷的账号密码不会因修改 `.env` 自动轮换**，需按 PostgreSQL 的账号迁移流程处理；请先备份，不要为改密码直接删除卷。

当前 Worker 容器仍以 root 运行以写入共享的 `data/` 目录；虽然 Web/API 端口只绑定本机，这套配置并非面向公网的生产加固方案。若日后扩展为共享私域部署，需要先完成非 root 权限、密钥管理、访问控制和备份策略。

## 验收与排查

```bash
docker compose ps
docker compose logs --tail=100 api worker db redis web
docker compose exec worker celery -A app.tasks:celery_app inspect ping
FACTORLAB_SMOKE_PASSWORD=research12345 python3 tools/verify_compose_stack.py
```

如果修改了研究员密码，把验收命令中的演示密码换成实际密码。该脚本使用已发布的 `demo_daily` 数据集提交一次单因子研究，轮询成功状态、检查执行日志、报告 HTML 与目录记录的 SHA-256；每运行一次会在数据库和 `data/runtime/artifacts/` 中留下一条真实验收记录。当前脚本还核对同一任务的 JSON 复现包、结果与报告双摘要；摘要一致仅表示导出内部一致，不是签名或行情来源认证。2026-10-16 的隔离异步复测见 [`ASYNC_ACCEPTANCE_2026-10-16.md`](ASYNC_ACCEPTANCE_2026-10-16.md)。提交研究任务后，应在 API 返回的任务中看到由 `pending` 转为 `success`，Worker 日志出现对应任务，报告中心出现 HTML 报告。首次构建会下载基础镜像和 Python/Node 依赖，耗时取决于镜像仓库与包仓库的网络状态。

2026-10-12 在 macOS OrbStack 实测：五个服务启动，API 健康检查通过，Worker `inspect ping` 返回 `pong`；验收脚本创建的运行 `ca31ae86-3ac3-4253-8bdc-5d2518f7ee41` 达到 `success / 100%`，Worker 日志确认接收并完成，HTML 报告含 SVG 图表。该结论只覆盖本机演示数据，不代表真实 A 股数据源或 Windows 环境已经验收。

### 2026-10-14：历史沪深 300 私有包的隔离容器验收

本次为避免改动已有 `fbl` 容器及数据库，使用单独的 Compose 项目 `factorlab-hs300-qa`、单独 PostgreSQL 命名卷和 `/private/tmp/fbl-hs300-qa-runtime` 运行目录；只启动 db、redis、api、worker，不启动 web，也不向宿主机发布 API 端口。API 与 Worker 仍共同挂载仓库 `data/`，因此能读取同一份未纳入 Git 的 `data/real/bundles/hs300_2024_0375298bd2c8ac52`。这属于本机私有验收环境，不是可分发的公开测试夹具。

新构建的 API、Worker 镜像各自一次性加载历史包并计算 `momentum_20d`，均得到 292 个行情日、242 个 2024 年成分交易日、328 只股票及 72,366 条有效因子观察。隔离环境中注册并发布该包后，通过 Redis 向 Celery 提交专用历史研究任务 `f7e564f0-b0bb-471b-aa9c-210cb35f1b0b`：Worker 日志确认收到任务并于约 6.52 秒后完成；数据库状态为 `success`，生成 43,427 字节 HTML 报告，报告完整性读取通过，再现性包含非空结果和报告 SHA-256。源数据目录记录 95,776 行。此次验证覆盖容器内私有包可见性、队列执行与产物完整性，不覆盖公网/多人安全加固、Windows 或容器前端浏览器流程；浏览器流程见 [`HS300_BUNDLE.md`](HS300_BUNDLE.md)。

复现时应先确认私有包存在并通过 `tools/verify_hs300_bundle.py`，且避免对已有项目使用 `down -v`。隔离项目需要独立的 Compose override：清空 API 发布端口，把 API/Worker 的 `/data/runtime` 同时绑定到一个临时目录，再以 `docker compose -p factorlab-hs300-qa -f docker-compose.yml -f <override文件>` 构建并启动 `db redis api worker`。验收结束只对**准确的隔离项目名及其测试卷**执行 `down -v`；不能省略 `-p` 或把此命令用于 `fbl`。

只停止容器并保留数据：`docker compose down`。不要在需要保留数据时使用 `docker compose down -v`，后者会删除数据库卷。Mac 上关闭 OrbStack 可用 `orb stop`，但这会影响本机其他容器项目，应先确认没有其他工作负载。

Windows + WSL2 的最终验收仍需在 Windows 主机重复；本页只记录 macOS 的 OrbStack 方式。

### 2026-10-14：现有栈更新与审计 CSV 容器验收

在确认 Alembic 已为 `20261010_0004 (head)`、既有 26 条任务全部完成且没有待运行任务后，构建最新 API、Worker、Web 镜像，并仅以 `docker compose up -d --no-deps --force-recreate api worker web` 替换这三个服务；PostgreSQL、Redis 与其数据卷没有重建或删除。更新后五个服务正常，API、Worker、数据库、Redis 健康，宿主机 `/health` 与网页入口可达；`tools/check_demo_readiness.py` 的五项只读预检通过，Worker 定向 `ping` 返回 `pong`。既有任务数仍为 26。

由于现有 `fbl` 数据库没有历史任务，成功下载路径另用 `factorlab-hs300-csv-qa` 隔离 Compose 项目验证。独立数据库、Redis、运行目录与不发布宿主机 API 端口的设置避免污染演示栈；仓库中 Git 忽略的私有历史包由 API/Worker 共同读取。经 HTTP 注册并发布历史包、提交历史任务后，Celery 任务 `6a006e4a-d513-4f3f-aa21-e103d2cfcf14` 成功；以研究员身份通过容器 API 下载复现 JSON、逐日 CSV、无标签 CSV，响应均带附件文件名。独立核对工具确认 4 个因子、968 行逐日审计、32 条无标签信号。该隔离项目的容器、网络、专用 PostgreSQL 测试卷已按准确项目名删除；主 `fbl` 栈和 26 条既有任务保留。临时导出文件仅位于 `/private/tmp/fbl-hs300-csv-qa-runtime/csv-qa/`，不纳入 Git。

此验收证明当前 macOS/OrbStack 镜像中的 API→Redis→Worker→HTTP 审计下载链路；不代表 Windows、多人并发或生产级安全已经验收。

### 可重复的隔离历史任务验收工具

`tools/verify_historical_api_journey.py` 把注册/发布私有包、提交历史任务、等待 Worker、下载复现 JSON、两份 CSV 和 HTML 报告、核对审计及报告摘要串成一次验收。**它会写入数据集和任务记录**，必须先准备独立 Compose 项目；命令行还要求显式传入 `--acknowledge-isolated-writes`。输出目录必须不存在，工具拒绝覆盖已有证据。没有本机封存包时无法运行。

Mac 上可在仓库外创建临时 override（路径按本机实际调整），使 API 只发布隔离的 18000 端口，并让 API/Worker 共享隔离运行目录：

```yaml
services:
  api:
    ports: !override ["127.0.0.1:18000:8000"]
    volumes:
      - /private/tmp/factorlab-hs300-qa-runtime:/data/runtime
  worker:
    volumes:
      - /private/tmp/factorlab-hs300-qa-runtime:/data/runtime
```

先用 `docker compose -p factorlab-hs300-qa -f docker-compose.yml -f <override文件> up --build -d db redis api worker` 启动。然后在宿主机设置 `FACTORLAB_HISTORICAL_ADMIN_PASSWORD` 和 `FACTORLAB_HISTORICAL_RESEARCHER_PASSWORD`，运行：

```bash
python3 tools/verify_historical_api_journey.py \
  --api-url http://127.0.0.1:18000/api/v1 \
  --bundle-id hs300_2024_0375298bd2c8ac52 \
  --output-dir /private/tmp/factorlab-hs300-qa-evidence \
  --acknowledge-isolated-writes
```

不要对主 `fbl` 栈使用这条写入式命令。确认测试项目名后，仅对它执行 `docker compose -p factorlab-hs300-qa -f docker-compose.yml -f <override文件> down -v` 清理其测试数据库卷；导出证据目录不会被此命令删除。Compose 普通端口列表会与基础文件叠加，因此要用 `!override` 替换端口列表，否则仍会尝试占用主栈的 8000 端口。
