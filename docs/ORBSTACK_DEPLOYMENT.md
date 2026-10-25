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

`docker compose ps` 中 Web、数据库、Redis、API 和 Worker 均应显示 `healthy`；Web 只检查容器内首页 HTTP 响应，Worker 则向当前容器对应的 Celery 节点发送定向 `ping`，不是只检查进程存在。Web 健康不替代宿主机 `curl` 或浏览器业务验收。

2026-10-19 本机 OrbStack 重启后，针对现有 `fbl` 项目从当时未提交工作区重新构建 API、Worker、Web 镜像，仅强制重建这三个应用容器；数据库和 Redis 未重建。更新前后数据库版本数均为 2，宿主机网页及 `/health` 均返回 200，管理员登录后只读数据列表也返回 2 个版本。镜像与限制见 [CHG-20261019-018](changes/2026-10-19-018-orbstack-current-worktree-refresh.md)。此记录不代表随后修改的代码已自动进入容器。

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
FACTORLAB_SMOKE_URL=http://127.0.0.1:8000/api/v1 \
FACTORLAB_SMOKE_PASSWORD=research12345 \
python3 tools/verify_compose_stack.py --acknowledge-writes
```

运行前须核对 `FACTORLAB_SMOKE_URL` 指向准备写入的目标，建议优先使用隔离栈端口。两个 Compose 写入式验收脚本都要求显式 URL 和 `--acknowledge-writes`；这只是防误操作门槛，指向主栈仍会写入主栈。

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

2026-10-25 已把历史私有包隔离配置固化为 `docker-compose.historical-qa.yml` 与 `tools/verify_historical_qa_compose.py`。它要求唯一 `factorlab-historical-qa-*` 项目名、系统临时目录中的全新运行目录、独立 PostgreSQL 卷与网络、本机 15122/18022 端口、演示 CSV 和私有包只读挂载。实际两条当前源码真实任务通过 API→Celery→四文件导出→离线复算；首次临时配置漏挂演示 CSV 的失败及修复均留档。见 [异步验收记录](HISTORICAL_ASYNC_ACCEPTANCE_2026-10-25.md)。下一次优先使用新配置和预检；以下临时 override 仅保留为旧方法参考。

`tools/verify_historical_api_journey.py` 把注册/发布私有包、提交历史任务、等待 Worker、下载复现 JSON、两份 CSV 和 HTML 报告、核对审计及报告摘要串成一次验收。**它会写入数据集和任务记录**，必须先准备独立 Compose 项目；命令行还要求显式传入 `--acknowledge-isolated-writes`。输出目录必须不存在，工具拒绝覆盖已有证据。没有本机封存包时无法运行。

验收还核对复现包中的任务 ID、成功状态、数据集 ID、封存包 ID 与五分组参数必须对应本次提交；四文件内部一致但属于其他任务时不算通过。

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

### 2026-10-19 当前主栈浏览器闭环

在 CHG-20261019-018 更新应用镜像后，当前 `fbl` 主栈已完成一次管理员浏览器验收：三行合成 CSV 的旧预览在换文件后失效，重新预览、导入、顶部周末提醒与发布均成功；新版本为 `compose_accept_20261019 / 20261019.133241.102062`。再用原有 `demo_daily / 0.2.0` 执行 20 日动量单因子研究，Run `56b06bd9-7d61-4b2b-aa17-19e1b7e101e6` 成功，报告在线预览与 HTML 下载完成。主栈原有数据保留，新增测试版本和任务不清理。详细记录、SHA-256 与截图见 [CHG-20261019-019](changes/2026-10-19-019-compose-browser-end-to-end-qa.md)。这是 Mac/OrbStack 软件链路验收，不代表真实投资绩效或 Windows 验收。

### 2026-10-19 研究页所选版本提醒上线

只重建并替换 Web 容器，镜像 SHA-256 为 `d2c4d98f613d935b6d7ad6e1afb126506a2eaf2093337c5cd84a349d92dc181f`；其余四服务未重建且状态正常。管理员浏览器中，选中含周末行情的 `compose_accept_20261019` 时提醒可见，改选正常的 `demo_daily` 后提醒消失。总览仍有 3 个数据版本、27 个成功任务和 27 份报告。截图和限制见 [CHG-20261019-021](changes/2026-10-19-021-research-warning-orbstack-browser-qa.md)。

### 2026-10-20 公告休市诊断与合成数据告知上线

确认 27 个任务均已成功且无运行/排队任务后，只替换 API、Worker、Web；DB、Redis 和数据卷保留。五服务正常，版本数仍为 3，任务和报告仍各为 27。浏览器数据页可见旧验收样本周末风险及演示版本 11 日/220 行公告休市合成行情告知；研究页切换选中版本时提示同步变化。详细镜像 SHA、截图及未覆盖边界见 [CHG-20261020-003](changes/2026-10-20-003-calendar-orbstack-deployment-browser-qa.md)。旧质量报告未回填，2024–2025 公告休市诊断不等于完整交易日历。

### 2026-10-20 报告风险披露上线

再次确认无在途任务后定向更新 API、Worker、Web；浏览器中的旧演示报告外层出现合成数据限制，切到 BaoStock 报告后消失。数据库仍为 3 个版本、27 个任务、27 个报告产物；旧报告文件不改写。镜像、截图和范围见 [CHG-20261020-004](changes/2026-10-20-004-report-dataset-risk-disclosure.md)。

### 2026-10-20 报告披露版交付上线

报告中心默认下载带数据身份、原报告 SHA 与风险说明的派生 HTML；原始归档下载 API 与存储文件不变。仅重建 API、Worker、Web，主栈仍为 3 个版本、27 个任务、27 个报告产物。浏览器点击与本机 HTTP 双接口摘要核对见 [CHG-20261020-005](changes/2026-10-20-005-report-disclosed-delivery-copy.md)。

### 2026-10-20 离线休市规则扩展至 2026 年

依据沪深两所正式公告将共同休市区间扩展到 2026 年，规则版本升至 `sse-szse-announced-closures-2024-2026-v2`。只更新 API/Worker，五服务正常；运行容器验证 2026-10-07 命中、10-08 不命中。既有 3 个数据版本、27 个任务与 27 个报告产物未变；旧质量报告未回填。来源、镜像与边界见 [CHG-20261020-006](changes/2026-10-20-006-2026-announced-closure-coverage.md)。

### 2026-10-20 适配预览日期明细上线

预览接口现返回完整公告休市命中日期和规则版本，页面在导入前展示。仅替换 API、Worker、Web；用临时 2026 CSV 对主栈只做预览，返回 2026-10-07 与 v2 规则，不创建版本。主栈仍为 3 个版本、27 个任务、27 个报告。测试、镜像身份和浏览器未覆盖边界见 [CHG-20261020-007](changes/2026-10-20-007-adapter-calendar-preview-provenance.md)。

### 2026-10-20 预览浏览器实点与无关警告修复

浏览器选择两行本机合成 CSV、点击适配预览，页面显示 2026-10-07 与 v2 规则。发现无成交量列仍提示单位核对后，适配器升至 1.3.1，仅更新 API/Worker 并浏览器复点，误报消失；未执行导入，主栈 3 版/27 任务/27 报告不变。见 [CHG-20261020-008](changes/2026-10-20-008-calendar-preview-browser-qa-and-volume-warning.md)。

### 2026-10-20：报告公告休市风险传递

更新前只读确认无在途任务，主栈为 3 个数据版本、27 个成功任务、27 份报告。后端 237 项、前端 42 项通过且 Web 构建成功后，仅重建并替换 API、Worker、Web；DB/Redis/数据卷保留。更新后数量仍为 3/27/27。报告中心外围可对绑定数据版本提示公告休市与未覆盖年份；新报告和派生披露版 HTML 带相同数据风险，历史归档 HTML 不回填也不改写。此次新质量字段分支由单元测试覆盖，未进行浏览器实点。详见 [CHG-20261020-009](changes/2026-10-20-009-report-calendar-risk-propagation.md)。实际执行者：Codex。

### 2026-10-20：报告风险隔离 HTTP 回归与 Web 更新

隔离 SQLite/TestClient 跑通预览、按原文件摘要导入、发布、研究任务、新报告、派生披露版及原归档字节复核。报告页面文案改为独立纯函数并核对 ID+SHA 双重匹配。后端 238 项、前端 43 项通过，生产构建成功。只替换 Web 容器，主栈仍为 3 版/27 成功任务/27 报告；五服务运行，Web 容器内部页面请求成功。宿主沙箱 `curl 127.0.0.1:5173` 未连通，本轮不声称浏览器实点。见 [CHG-20261020-010](changes/2026-10-20-010-calendar-report-http-journey.md)。实际执行者：Codex。

### 2026-10-21：Mac 浏览器只读验收与下载反馈 Web 更新

宿主机本地页面可访问；浏览器复点概览、数据集、研究页、报告中心与比较页。仅对已有报告发起派生披露版下载，不创建任务或导入数据。报告下载按钮新增发起提示及失败反馈；提示只确认浏览器下载请求已发起，不证明文件落盘。前端 45 项、后端 242 项通过且 Web 构建成功。仅重建并替换 Web，API/Worker/DB/Redis 保留；只读核对主栈仍为 3 个数据版本、27 个成功任务、27 份报告。见 [浏览器验收记录](MAC_BROWSER_ACCEPTANCE_2026-10-21.md)与 [CHG-20261021-004](changes/2026-10-21-004-mac-browser-readonly-qa-and-download-feedback.md)。实际执行者：Codex。

### 2026-10-21：报告下载内容守卫 Web 更新

前端 46 项测试和生产构建通过后，仅重建并替换 Web 镜像（SHA-256 `f65fcd673b4973117cf14b876610ef8a83accbac34e5f12f84bbb04b4b4fe355`）。API/Worker/DB/Redis 未替换，五服务运行；宿主机 `HEAD http://127.0.0.1:5173/` 返回 200。未重复数据库计数或浏览器下载落盘核对。见 [CHG-20261021-005](changes/2026-10-21-005-report-download-payload-guard.md)。实际执行者：Codex。

### 2026-10-21：专用 Compose 连续浏览器验收

新增 `docker-compose.browser-qa.yml`，只可配合显式唯一 `-p` 项目名与新建的 `FACTORLAB_QA_RUNTIME_DIR` 使用。覆盖配置将 Web/API 绑定本机 15121/18021、API/Worker 共享隔离目录，样本目录只读；数据库卷随项目名独立。实际使用 `factorlab-browser-qa-1021`，合并配置已核对不指向主栈数据；新合成 CSV 在同一浏览器完成导入发布、Worker 研究、报告预览与下载落盘字节核对。隔离栈结束前 2 版/1 任务/1 报告，主栈仍 3/27/27。验收后仅对精确隔离项目执行 `down`，不加 `-v`，专用测试卷与临时运行目录保留；主栈未动。详见 [连续验收记录](MAC_ISOLATED_BROWSER_JOURNEY_2026-10-21.md)与 [CHG-20261021-008](changes/2026-10-21-008-isolated-new-data-browser-journey.md)。实际执行者：Codex。

### 2026-10-21：隔离栈启动前预检

先用 `mktemp -d /private/tmp/factorlab-browser-qa-XXXXXX` 创建新的专用目录，设置唯一项目名，再运行 `tools/verify_browser_qa_compose.py --project-name <项目名> --runtime-dir <绝对目录>`。工具只解析 `docker compose config --format json`，核对项目、端口、网络、卷、CORS、数据库与队列地址及挂载；PASS 后**仍须用完全相同**的 `-p` 和目录执行 `up`。不要对主 `fbl` 项目使用本覆盖文件。正反例及上轮隔离配置实测通过，后端 249 项通过；未重新启动隔离服务。见 [CHG-20261021-009](changes/2026-10-21-009-browser-qa-compose-preflight.md)。实际执行者：Codex。
