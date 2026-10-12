# 量化投资多因子研发平台

面向课程验收的私有部署多因子研究平台。当前仓库包含可离线复现的“版本化数据 → 六因子目录 → 单因子检验 → 结果与报告”链路。

## 目录

- `backend/`：FastAPI 接口、领域模型和纯 Python 研究计算核心。
- `frontend/`：React + TypeScript 研究工作台。
- `data/sample/`：固定演示数据。
- `data/real/`：本地自行获取的真实 A 股小样本，默认不纳入 Git；来源与获取步骤见 [`docs/REAL_A_SHARE_SAMPLE.md`](docs/REAL_A_SHARE_SAMPLE.md)。
- `docs/`：PRD、计划、学习路线和个人验收模板。
- [`docs/CHANGE_INDEX.md`](docs/CHANGE_INDEX.md)：从当前基线起，统一索引每次修改的内容、代码位置、决策过程和验证证据。
- `docker-compose.yml`：Web、API、Worker、PostgreSQL、Redis 的统一编排。

## 本地启动

macOS 可使用 OrbStack，Windows 端可使用 Docker Desktop + WSL2。两者均运行同一份 Compose 文件；Mac 具体步骤见 [`docs/ORBSTACK_DEPLOYMENT.md`](docs/ORBSTACK_DEPLOYMENT.md)：

```bash
docker compose up --build
```

不创建 `.env` 时使用下面的本机演示账号。若需自定义密码或在多人环境部署，先复制 `.env.example` 为 `.env`，填写其中的数据库、JWT 和演示账号密码后再启动；示例文件里的 `replace-...` 都是占位值，不能直接用于共享部署。已有数据库中的账号密码不会因修改启动变量而自动更新。

打开：

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

未设置 `.env` 的首次启动会初始化三个课程演示账号：`admin / admin12345`、
`researcher / research12345`、`viewer / viewer12345`。管理员负责数据和用户管理，
研究员可以创建研究且只能查看自己的任务与报告，只读用户可以查看全部研究结果。
共享部署前必须通过 `.env` 修改默认密码和 `JWT_SECRET`，详细权限矩阵见
[`docs/AUTHORIZATION.md`](docs/AUTHORIZATION.md)。

登录后默认进入项目总览，集中展示数据版本、六个内置因子、任务状态、成功率、报告数量和近期研究活动。研究员只统计本人任务，管理员和只读用户查看全局汇总；口径见 [`docs/DASHBOARD.md`](docs/DASHBOARD.md)。

管理员可以在用户管理页面创建账号、配置角色并启停账号。停用后既不能重新登录，已有 Token 也会立即失效；管理保护规则见 [`docs/USER_MANAGEMENT.md`](docs/USER_MANAGEMENT.md)。

## 数据集导入

当前支持UTF-8 CSV的导入、质量检查、SHA-256校验和、草稿版本和发布操作。字段规范及接口流程见[`docs/DATASET_FORMAT.md`](docs/DATASET_FORMAT.md)。

导入发生磁盘写入或数据库提交错误时，会回滚数据库会话并清理本次新建的文件，避免普通失败路径留下孤儿数据。

部署或演示前可运行 `make audit-data` 巡检数据版本：报告丢失、校验和变化及未登记的 CSV 文件，不会自动修改数据；容器中可运行 `docker compose exec api python -m app.services.storage_audit`。详见 [`docs/DATASET_FORMAT.md`](docs/DATASET_FORMAT.md)。

管理员可以对 Tushare、BaoStock 和常见中文行情 CSV 执行字段映射预览与标准化导入。适配器只转换字段、日期和证券代码，不猜测成交量、换手率和市值单位；详见 [`docs/CN_DATA_ADAPTER.md`](docs/CN_DATA_ADAPTER.md)。

质量详情包含字段完整率、缺失数量、数值范围和前20行预览。预览和发布前都会重新校验文件内容；草稿文件丢失或内容变化时不会发布。

前端左侧“数据集”页面可以完成上传和发布；研究工作台只列出已发布版本。创建实验时会固定数据版本ID，Worker执行前再次核对文件校验和，文件内容被修改时任务将失败并留下错误摘要。

“任务中心”展示全部历史Run并自动刷新运行状态。选择任务后可以查看数据版本、因子版本、后端源码指纹、完整参数、执行时间、错误摘要和结构化指标结果。Worker 会在执行前核对代码指纹；口径见 [`docs/CODE_VERSION.md`](docs/CODE_VERSION.md)。

任务中心可下载 JSON 复现包，汇总数据校验和、因子公式与版本、参数、代码指纹、结果及摘要校验和、报告校验和和任务日志。复现包不包含原始数据或报告文件；跨机器重新计算仍需要相同数据和代码。

任务中心同时展示持久化执行日志。等待任务可以立即取消，运行中任务采用Worker阶段间协作取消；失败或取消任务可以生成新的重试实验。具体状态机和接口权限见 [`docs/TASK_EXECUTION.md`](docs/TASK_EXECUTION.md)。

“实验对比”支持选择 2—6 个成功任务，统一展示核心指标、相对基准差值和排名，并自动检查数据版本、分组数和共同日期。结果可导出为 Excel 友好的 CSV 或可打印的独立 HTML 报告。见 [`docs/EXPERIMENT_COMPARISON.md`](docs/EXPERIMENT_COMPARISON.md)。

研究成功后，Worker会同时生成带SHA-256校验和的独立HTML报告，内嵌IC与多空净值SVG曲线，无需外部图表服务。“报告中心”支持历史报告预览和下载，浏览器可直接打印为PDF。预览和下载前会重新核对文件校验和；文件丢失返回 `410`，内容被修改返回 `409`，避免将损坏报告误当成原始研究结论。

“因子库”提供动量、反转、波动率、换手率、总市值和市盈率六个内置因子。仓库自带的 20 只虚拟股票、120 个交易日全字段数据可直接运行全部六个因子。公式与边界见 [`docs/FACTOR_CATALOG.md`](docs/FACTOR_CATALOG.md)。
演示数据的生成、限制和性能验收方法见 [`docs/DEMO_DATA.md`](docs/DEMO_DATA.md)。

单因子检验支持 MAD 去极值、截面标准化、IC/Rank IC、ICIR、IC胜率、IC 分布、分组净值、多空净值和头部组换手率。工作台与报告均展示各组净值曲线；工作台和报告中的 IC 空值不会被画成零。指标定义及未包含的交易假设见 [`docs/SINGLE_FACTOR_ANALYSIS.md`](docs/SINGLE_FACTOR_ANALYSIS.md)。

课程验收可运行 `make golden`，将固定小样本的因子值、IC、分组收益和成本后收益与手算常数逐项比较；输入和算式见 [`docs/GOLDEN_RESEARCH_VERIFICATION.md`](docs/GOLDEN_RESEARCH_VERIFICATION.md)。

成功任务会基于固定规则生成“结论—证据—限制—下一步”草稿，不调用模型且必须由研究人员复核。规则与风险边界见 [`docs/RESEARCH_CONCLUSION.md`](docs/RESEARCH_CONCLUSION.md)。

研究任务可以设置因子起止日期、证券代码列表和 2—10 个分组。计算时保留起始日前的回看历史，样本规则见 [`docs/SAMPLE_SELECTION.md`](docs/SAMPLE_SELECTION.md)。

研究任务可选择直接使用导入的 `close`，或使用 `close × adj_factor` 计算价格因子与下一日收益。价格口径写入参数、结果和报告；分拆日样例与输入约束见 [`docs/PRICE_BASIS.md`](docs/PRICE_BASIS.md)。

研究任务可设置 0—100 bps 单边成本，同时查看毛多空收益和成本后收益、净值曲线。计算包含首次建仓及换仓的买卖两侧，模型假设见 [`docs/TRANSACTION_COSTS.md`](docs/TRANSACTION_COSTS.md)。

研究工作台还支持选择 2—6 个因子进行等权合成，输出共同样本覆盖量、实际权重和因子相关矩阵。合成顺序、缺失值处理和限制见 [`docs/MULTI_FACTOR_ANALYSIS.md`](docs/MULTI_FACTOR_ANALYSIS.md)。

```bash
curl -X POST http://localhost:8000/api/v1/datasets/import \
  -H "Authorization: Bearer <管理员登录后返回的access_token>" \
  -F dataset_key=course_demo \
  -F name=课程演示数据 \
  -F file=@data/sample/daily_prices.csv
```

导入后根据返回的`id`发布：

```bash
curl -X POST http://localhost:8000/api/v1/datasets/<id>/publish \
  -H "Authorization: Bearer <管理员登录后返回的access_token>"
```

不使用 Docker 时，需要 Python 3.12+ 和 Node.js 20+：

```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -e './backend[dev]'
(cd backend && alembic upgrade head)
cd frontend && npm install && npm run dev
```

若前端不在默认的 `http://localhost:5173`，启动 API 前设置 `CORS_ORIGINS` 为实际前端地址；多个地址用英文逗号分隔。该设置只控制浏览器跨域访问，不应填 `*` 用于共享部署。

另开终端执行 `make api`。核心算法测试不需要第三方 Python 包：

```bash
make test
```

每次推送和拉取请求会触发 [GitHub Actions CI](.github/workflows/ci.yml)，分别在 Linux 和 Windows 上执行后端测试、固定样例校验和前端生产构建。CI 只使用隔离的 SQLite 测试数据库，不启动 PostgreSQL、Redis 或 Docker；完整 Compose 联调仍按 [`docs/ORBSTACK_DEPLOYMENT.md`](docs/ORBSTACK_DEPLOYMENT.md) 与 [`docs/MAC_E2E_ACCEPTANCE.md`](docs/MAC_E2E_ACCEPTANCE.md) 本地验收。

后端测试含一条隔离环境中的完整 API 旅程：管理员上传并发布 CSV、研究员运行因子、查看日志并下载复现包和报告，同时验证未登录、只读及其他研究员的权限。它不代替浏览器 UI 或 Windows 实机验收。

## 当前阶段边界

研究实验和任务已经使用数据库持久化。Docker Compose 使用 PostgreSQL、Redis 和 Celery Worker；不使用 Docker 时默认采用 SQLite 和内联执行模式，方便在 macOS 或 Windows 上快速调试。

技术选型所参考的量化与实验平台、采用范围和许可证注意事项见 [`docs/OPEN_SOURCE_RESEARCH.md`](docs/OPEN_SOURCE_RESEARCH.md)。

第一次导师阶段汇报初稿见 [`docs/FIRST_MENTOR_REPORT.md`](docs/FIRST_MENTOR_REPORT.md)。

Mac 本地端到端验收的已通过步骤、环境限制和复现方法见 [`docs/MAC_E2E_ACCEPTANCE.md`](docs/MAC_E2E_ACCEPTANCE.md)。

截至 2026-10-12 的成果、PRD 差距与后续计划见 [`docs/PROJECT_STATUS_2026-10-12.md`](docs/PROJECT_STATUS_2026-10-12.md)。
扩展项的价值、数据前提和建议顺序见 [`docs/EXTENSION_OPTIONS.md`](docs/EXTENSION_OPTIONS.md)。

300 只股票、3 年日频的单因子性能基准可运行 `make benchmark-prd`；Mac 实测结果和计时边界见 [`docs/PERFORMANCE_ACCEPTANCE.md`](docs/PERFORMANCE_ACCEPTANCE.md)。
