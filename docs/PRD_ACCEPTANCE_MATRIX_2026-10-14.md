# PRD—实现—测试证据对照表（初建 2026-10-14；更新 2026-10-21）

本表供队长控制范围和课程汇报使用。逐项对照 [`PRD.md`](PRD.md) V1.0，区分“代码存在”“本机验证”“目标环境验收”。按队长 2026-10-16 约定，开发者每轮代执行并更新 A/B/C/D 四责任包材料，无须成员个人签收；必须如实写明执行者，测试或脚本通过也不等于研究结论有效。最近一次本机自动化记录为后端 261 项、前端 50 项（均为 2026-10-23）通过；新数据连续 Mac 浏览器证据见 [隔离栈记录](MAC_ISOLATED_BROWSER_JOURNEY_2026-10-21.md)。Windows 部署目前不在本轮执行范围。下方 10 月 14—17 日运行记录保留为历史证据，不冒充最新运行结果。

2026-10-22 补充：Web 镜像使用锁文件安装后，隔离五服务已成功构建启动，Web 入口与 API 的 HTTP 检查通过，见 [构建记录](changes/2026-10-22-008-web-lockfile-image-build.md)。本轮未重做容器化浏览器互动；前次价格口径页面实点仍是本机 Vite 连接隔离 API，不应混称为 Web 容器页面验收。

2026-10-22 再补充：随后已完成 [容器化 Web 浏览器实点](MAC_CONTAINER_PRICE_BASIS_BROWSER_QA_2026-10-22.md)：研究员登录后单因子/等权多因子的错误复权口径被禁用，改回导入价后恢复。上段“未重做容器化浏览器互动”只描述 CHG-008 当轮；本轮未新建任务、未重做报告链路，也非队长本人验收。

2026-10-22 运行状态补充：Web 容器增加首页 HTTP 健康检查，隔离项目五服务均实测 `healthy`，见 [CHG-20261022-010](changes/2026-10-22-010-web-healthcheck.md)。该状态仅证明容器内部检查通过，不等于宿主机访问、业务流程或主栈已部署新配置。

2026-10-22 价格字段补充：数据版本缺少 `adj_factor` 整列时，`factor_adjusted` 单因子/多因子提交前即返回 400 且不建任务，前端同步提示，见 [CHG-20261022-011](changes/2026-10-22-011-missing-adjustment-column-preflight.md)。本轮仅本机自动化，未部署 Web/API 容器；列存在也不证明数值或复权定义正确。

2026-10-22 隔离验收补充：上述缺列守卫随后已在 [容器页面与 API](MAC_MISSING_ADJ_FACTOR_BROWSER_QA_2026-10-22.md) 实点；合成版本只存在专用卷，单因子/多因子页面禁用与两类 HTTP 400 均确认。前段“未部署容器”为 CHG-011 当轮状态；本轮未重算研究指标，也非队长本人验收。

2026-10-23 样本范围补充：[部分缺失乘数的提交前校验](changes/2026-10-23-001-partial-adjustment-sample-preflight.md)仅对未指定证券的全样本调整价研究使用全版本缺失计数；指定证券的有效子集在隔离 HTTP 测试可成功。尚未做容器浏览器实点，逐行乘数及真实复权定义仍需另行核验。

2026-10-23 逐证券补充：[新导入版本的缺失归属](changes/2026-10-23-002-symbol-adjustment-missing-evidence.md)现可对受影响的指定证券在提交前拒绝，其他完整证券仍能研究。旧版本无此质量字段时不回填、不猜测；本轮仅本机自动化，尚无容器页面实点。

2026-10-23 容器实点补充：[隔离 QA 记录](MAC_SYMBOL_ADJ_GAP_BROWSER_QA_2026-10-23.md)验证了新版本导入发布、全样本/受影响子集单因子和等权多因子禁用、完整子集按钮恢复；研究任务/报告均未增加。上一段“尚无容器页面实点”为 CHG-002 当时状态。本轮未实际执行完整子集，不作为 Worker 成功或真实市场验收。

2026-10-23 Worker 补充：[隔离执行记录](MAC_SYMBOL_ADJ_GAP_WORKER_QA_2026-10-23.md)现证明完整证券子集在容器 Worker 中成功并归档可交付报告，受影响子集 API 400 不增任务；上一段“未实际执行”为 CHG-003 当时状态。本轮是 API 合成样本验收，不代表浏览器提交或真实样本因子有效性。

2026-10-23 浏览器闭环补充：[页面运行记录](MAC_SYMBOL_ADJ_GAP_BROWSER_RUN_2026-10-23.md)完成容器 Web 研究员点击运行→任务中心成功→报告中心同 Run 归档→披露版 HTML 下载。上一段“不代表浏览器提交”为 CHG-004 当时状态；仍仅合成数据软件验收，非真实样本研究或 Windows 验收。

2026-10-23 报告口径补充：[CHG-20261023-006](changes/2026-10-23-006-adjustment-report-scope-disclosure.md)使新调整价报告及交付副本披露全版本缺失乘数，不把完整子集成功外推到其他证券。后端 262 项通过；既有归档未回写，容器页面尚未复验此新文案。

2026-10-23 HTTP 回归补充：[CHG-20261023-007](changes/2026-10-23-007-adjustment-report-http-regression.md)覆盖隔离导入→发布→完整子集调整价研究→归档/交付副本，验证缺乘数文案、原始归档不变及原始导入价不误报。仍为本机 TestClient 合成数据测试，非容器页面实点。

2026-10-23 容器补充：[隔离报告记录](MAC_ADJUSTMENT_REPORT_CONTAINER_QA_2026-10-23.md)验证新 Worker 归档显示全版本缺乘数警告、交付副本 SHA 头一致，旧归档 SHA 不变。上一段“非容器”仅指 CHG-007 当时；本轮仍非新文案浏览器实点或真实数据验收。

2026-10-23 来源边界补充：[CHG-20261023-009](changes/2026-10-23-009-imported-csv-provenance-disclosure.md)让普通 CSV 新报告和交付副本披露真实性、授权及完整交易日历未认证，避免把质量检查“通过”误写成来源认证。后端 263 项通过；本轮未更新容器或实点页面，旧归档不回写。

2026-10-23 页面边界补充：[CHG-20261023-010](changes/2026-10-23-010-imported-csv-provenance-ui.md)让数据集、研究与报告页面同步提示普通 CSV 认证边界；报告中心必须匹配数据版本 ID 和 SHA，避免错配提示。前端 51 项与构建通过，尚未容器实点，且不自动核实真实数据来源。

2026-10-23 容器页面补充：[隔离实点记录](MAC_CSV_PROVENANCE_BROWSER_QA_2026-10-23.md)确认普通 CSV 提醒在数据集/研究/报告三处可见、不阻断研究，切换内置演示版后改显示专属说明。上一段“尚未容器实点”为 CHG-010 当时状态；仍不代表真实来源/授权得到认证或队长本人已验收。

状态：**已验（Mac）**＝有本机自动测试或实测证据；**部分**＝流程存在但 PRD 口径尚缺项；**未验**＝尚无目标环境实测；**未实现**＝没有相应功能。私有真实行情包在 Git 忽略目录中，不能把仓库代码误称为“任意电脑开箱复现真实样本”。

## 功能与验收矩阵

| PRD 条款与验收点 | 当前状态 | 实现位置与现有证据 | 剩余工作／放行条件 |
| --- | --- | --- | --- |
| §3、§5.1：登录、三角色、后端资源权限 | 已验（Mac） | `backend/app/auth.py`、`backend/app/main.py` 登录与权限路由；`backend/tests/test_auth.py`、`test_api_journey.py`；[多账号浏览器验收](changes/2026-10-18-003-multi-account-browser-qa.md) | A/B/C/D 为 Codex 代执行材料，不冒充成员各自亲测；Windows 暂缓 |
| §5.2：CSV 导入、质量校验、SHA-256、发布不可变版本 | 已验（Mac）；完整交易日历未实现 | `backend/app/services/datasets.py`、`backend/tests/test_datasets.py`；[`DATASET_FORMAT.md`](DATASET_FORMAT.md)；[新数据连续隔离浏览器验收](MAC_ISOLATED_BROWSER_JOURNEY_2026-10-21.md)、[公告休市容器复点](changes/2026-10-20-003-calendar-orbstack-deployment-browser-qa.md) | B 继续保留来源、字段和异常样本；公告规则仅覆盖已封存年份，不等于完整开市日历、临时休市或停牌核验，旧版本不自动回填 |
| §4、§5.2、§7：Parquet 导入及 DuckDB/Parquet 大数据存储 | 未实现 | 当前入口为 CSV；PostgreSQL 存元数据，历史包为封存 CSV；[`PROJECT_STATUS_2026-10-12.md`](PROJECT_STATUS_2026-10-12.md) 已列为缺口 | 属 PRD 与当前实现的显式偏差；在课程评分要求确认前不扩大范围，最终需修订 PRD 或实现并实测 |
| §5.2：证券主表、日历、复权、行业历史、基准行情与财务披露时点 | 部分 | CSV 字段和价格口径见 [`DATASET_FORMAT.md`](DATASET_FORMAT.md)、[`PRICE_BASIS.md`](PRICE_BASIS.md)；适配来源 `adjustflag` 在新报告/交付副本披露但不作乘数，见 [`CN_DATA_ADAPTER.md`](CN_DATA_ADAPTER.md)；历史包含日历、成员、行情、交易/ST 状态 | 来源状态仍须与原数据核对；行业历史、完整基准和财务公告时点未形成通用数据链路；不得宣称财务无前视偏差 |
| §5.3：六个版本化内置因子 | 已验（Mac），真实样本有限制 | `backend/app/domain/factors.py::FACTOR_REGISTRY`、`backend/app/services/catalog.py`；`backend/tests/test_factors.py` | 演示 CSV 可覆盖六因子；真实 BaoStock 样本不含总市值，2024 历史包仅跑四个价格/换手率因子；C 需明确解释差异 |
| §5.4：样本／日期选择、MAD 去极值、Z-score、异步任务 | 已验（Mac） | `backend/app/services/runs.py`、`backend/app/tasks.py`、`backend/app/domain/research.py`；`backend/tests/test_research.py`、`test_api_journey.py`；[隔离浏览器同一新版本 Worker 任务与日志](MAC_ISOLATED_BROWSER_JOURNEY_2026-10-21.md)；[已复权来源提交前防重复调整](changes/2026-10-22-005-early-double-adjustment-guard.md)及[研究页浏览器实点](MAC_PRICE_BASIS_BROWSER_QA_2026-10-22.md) | 复权口径页面实点采用本机 Vite，非 Web 容器；未提交新任务；队长本人产品实测仍待补；普通 CSV 仍无独立交易所日历 |
| §5.4：行业与市值中性化 | 未实现 | [`SINGLE_FACTOR_ANALYSIS.md`](SINGLE_FACTOR_ANALYSIS.md) 记录边界 | 保持为缺口；若导师明确要求，先取得行业/市值时点数据及黄金结果，再评估实现量 |
| §5.4：进度、日志、取消、失败重试 | 已验（Mac） | `backend/app/main.py` 任务路由、`backend/app/services/runs.py`；`backend/tests/test_persistence.py`、`test_api_journey.py`；[`TASK_EXECUTION.md`](TASK_EXECUTION.md) | D 用失败/取消样例记录界面验收证据 |
| §5.5：IC、Rank IC、ICIR、分组／多空净值、换手率、成本口径 | 已验（Mac），非实盘回测 | `backend/app/domain/research.py`；`backend/tests/test_research.py`；[`GOLDEN_RESEARCH_VERIFICATION.md`](GOLDEN_RESEARCH_VERIFICATION.md)；[严格同样本 IC 手算黄金样本](MATCHED_COMPARISON_GOLDEN.md)；[`SINGLE_FACTOR_ANALYSIS.md`](SINGLE_FACTOR_ANALYSIS.md)；[10 月 15 日逐日均值](changes/2026-10-15-010-group-daily-mean-correction.md)、[并列值分组](changes/2026-10-15-011-deterministic-factor-ties.md)、[输入校验](changes/2026-10-15-012-research-observation-validation.md) | C 责任包继续保留独立黄金算式和差异证据；不得把统计检验等同于可成交收益；旧报告不自动按新口径重算 |
| §5.5、P1：历史沪深 300 成分与停牌/ST 可交易性 | 已验（Mac 私有包），来源边界未消除 | `backend/app/domain/historical_research.py`、`backend/app/services/historical_bundle.py`；[`HS300_BUNDLE.md`](HS300_BUNDLE.md)、[`INDEPENDENT_HS300_SPOTCHECK.md`](INDEPENDENT_HS300_SPOTCHECK.md)；[加载时字节复验](changes/2026-10-15-017-historical-load-snapshot.md) | 封存包需另行取得；成分生效时点、ST 源状态未全量独立核验；C/B 分别签收公式与来源证据 |
| P1：等权多因子及相关矩阵 | 已验（Mac） | `backend/app/domain/composite.py`、`backend/tests/test_composite.py`；[`MULTI_FACTOR_ANALYSIS.md`](MULTI_FACTOR_ANALYSIS.md)；[权重边界校验](changes/2026-10-15-014-composite-weight-validation.md) | IC 加权未实现；按已确认的课程范围保留等权，不把相关性解释为因果或独立增益 |
| §5.6：结构化结果、图表和独立 HTML 报告 | 已验（Mac，合成及私有历史包） | `backend/app/services/reports.py`、`backend/app/services/reproducibility.py`、`frontend/src/main.tsx`；`backend/tests/test_reports.py`、`test_reproducibility.py`；[新版本→Run→报告→浏览器文件字节核对](MAC_ISOLATED_BROWSER_JOURNEY_2026-10-21.md)；[私有历史包工作台、分页、报告预览与下载实点](HISTORICAL_BROWSER_PAGE_QA_2026-10-25.md) | 私有包历史浏览器闭环已验，但真实行情来源授权、独立公式和队长本人产品实测不由此证明 |
| §5.6、P1：PDF 导出 | 部分 | 浏览器可打印 HTML 为 PDF；[`README.md`](../README.md) 报告中心说明 | 无服务端 PDF 文件生成接口；答辩时如称“支持 PDF”，须限定为浏览器打印并实测 |
| §9.4：任务复现信息、文件和结果摘要 | 已验（Mac），跨机有条件 | `backend/app/services/reproducibility.py`；`backend/tests/test_reproducibility.py`；普通任务离线摘要核对见 [`REPRODUCIBILITY_EXPORT_CHECK.md`](REPRODUCIBILITY_EXPORT_CHECK.md)，历史四文件核对与当前源码只读复算见 [`HS300_BUNDLE.md`](HS300_BUNDLE.md)；[当前私有包 Celery→HTTP→复算](HISTORICAL_ASYNC_ACCEPTANCE_2026-10-25.md) | 复现包不包含原始私有行情及代码副本；2026-10-14 旧历史导出不符合当前口径且保留原样；新正例只在隔离栈，不是主栈；跨机复算须另备相同数据和代码 |
| §8：Web/API/Worker/PostgreSQL/Redis 私域 Compose 部署 | 已验（Mac OrbStack） | `docker-compose.yml`、`docker-compose.browser-qa.yml`、`docker-compose.historical-qa.yml`、[`ORBSTACK_DEPLOYMENT.md`](ORBSTACK_DEPLOYMENT.md)；[隔离栈新数据连续验收](MAC_ISOLATED_BROWSER_JOURNEY_2026-10-21.md)及[私有历史包五服务浏览器验收](HISTORICAL_BROWSER_PAGE_QA_2026-10-25.md) | Windows/WSL2 离线部署未验；当前只开放本机端口，不能宣称公网或多人生产级安全 |
| §2.3：300 股 × 3 年单因子完整检验 ≤60 秒 | 已验（单次 Mac 基准），目标环境未验 | [`PERFORMANCE_ACCEPTANCE.md`](PERFORMANCE_ACCEPTANCE.md) 记录完整 Run 1.614 秒、220,500 有效观察 | 需在最终推荐环境重复测量并记录硬件、版本；单次结果非通用性能保证 |
| §2.3：普通页面查询 ≤2 秒 | 部分（Mac HTTP + 浏览器抽样） | [`PAGE_QUERY_PERFORMANCE.md`](PAGE_QUERY_PERFORMANCE.md)：HTTP 六类入口最大 86.4 ms；三次已登录浏览器刷新 FCP 为 88/36/44 ms，五类切页各一次最大 150.7 ms | 浏览器切页仅单次样本，未覆盖真正冷启动、完整绘制、并发和 Windows；正式彩排及最终环境需重测 |
| §2.2、§12：10 分钟离线演示与四人独立责任包 | 部分 | [`DEMO_REHEARSAL.md`](DEMO_REHEARSAL.md) 有剧本与只读预检；[`FINAL_REHEARSAL_CHECKLIST.md`](FINAL_REHEARSAL_CHECKLIST.md) 为待执行清单；[`TEAM_PLAN.md`](TEAM_PLAN.md) 有四包划分；五服务浏览器异步闭环和四包代执行见 [`FULL_STACK_BROWSER_ACCEPTANCE_2026-10-16.md`](FULL_STACK_BROWSER_ACCEPTANCE_2026-10-16.md) | 当前用户要求暂不做演示；正式连续口头计时和队长产品实测保留为课程最终项，代执行材料不可表述为成员个人贡献 |
| §5.7：Ollama 摘要；P2 表达式编辑器 | 未实现，非首期放行项 | [`PRD.md`](PRD.md) 已列 P2 | P0 缺口和验收证据收齐前不启动 |

## 当前放行判断（2026-10-21）

- **可用于 Mac 课程软件功能证据**：登录与权限、CSV 版本化、六因子目录、异步研究、结构化结果、已有报告预览/披露版下载、单份浏览器文件与 API 字节一致性、隔离黄金样例和私有样本有限复核。各证据见上表与变更索引，不推断投资有效性。
- **仍为 PRD 显式偏差**：Parquet/DuckDB、行业/市值中性化、通用行业历史/基准/财务公告时点链路、服务端 PDF。不得仅因课程优先就把这些条款标为“已实现”；最终需修订 PRD 范围或完成实现与实测。
- **仍未放行的验收**：队长本人产品实测、十分钟正式演示计时、Windows 私域部署、真实行情再分发权利。单次新数据页面连续闭环已在 Mac 隔离栈用合成 CSV 完成；当前用户要求不做演示/Windows，故那些项目不阻塞当前 Mac 开发，但不能写成最终完成。

## 自动化与环境证据

- **工作台结果归属本机工作树（2026-10-16）**：前端构建、后端 191 项、固定六观测黄金验算通过；隔离浏览器确认配置变更隐藏旧指标、三分组新任务显示 `Q3 − Q1` 和新 Run ID，见 [`RESULT_PROVENANCE_BROWSER_QA_2026-10-16.md`](RESULT_PROVENANCE_BROWSER_QA_2026-10-16.md)。这是 SQLite 内联模式的页面行为，不是本次提交的 Celery、Windows 或正式十分钟演示验收。
- **前端配置回归本机工作树（2026-10-16）**：把同一请求参数构造和结果可见性抽为纯函数，Node 22 的 7 项前端测试、前端构建、后端 191 项及黄金验算通过；CI 已新增前端测试步骤，但其 Ubuntu/Windows 结果须按本提交另查。见 [`FRONTEND_CONFIGURATION_REGRESSION_2026-10-16.md`](FRONTEND_CONFIGURATION_REGRESSION_2026-10-16.md)。
- **研究参数提交前校验（2026-10-16）**：数字输入、样本日期和多因子成分在前端提交前给出明确错误；前端 9 项测试、生产构建、后端 191 项及黄金验算通过。未重新运行浏览器和队列；见 [CHG-20261016-022](changes/2026-10-16-022-research-input-preflight.md)。
- **研究轮询会话隔离（2026-10-16）**：退出登录后旧研究请求的迟到响应不再写回工作台或触发收尾刷新；前端 12 项、生产构建、后端 191 项与黄金验算通过。未进行新浏览器多账号点测，不代表取消服务端任务；见 [CHG-20261016-023](changes/2026-10-16-023-research-poll-session.md)。
- **任务／报告详情归属（2026-10-16）**：日志、规则结论和 HTML 预览仅在对应当前 Run 时显示，旧请求晚到会被忽略；前端 13 项、构建、后端 191 项及黄金验算通过。未重新做浏览器快速切换；见 [CHG-20261016-024](changes/2026-10-16-024-selected-detail-identity.md)。
- **当前浏览器及 CI 回归（2026-10-16）**：隔离 Mac 浏览器实测无效分组拦截与标签修正，两条合成 Run 的任务和报告切换正确，控制台错误／警告 0；Windows CI 从 `38382a4` 起失败，新增 LF 属性待新提交验证。见 [`CURRENT_BROWSER_AND_CI_QA_2026-10-16.md`](CURRENT_BROWSER_AND_CI_QA_2026-10-16.md)。
- **跨平台 CI 后验（2026-10-17）**：LF 修正提交 `3c926d5` 的 [运行 #39011360370](https://github.com/cangshan-cloud/PBL/actions/runs/39011360370) 在 Ubuntu／Windows 两个 Verify 作业均成功；只验证工作流内的单测、黄金验算和前端构建，不代表 Windows Docker 部署。见 [CHG-20261017-001](changes/2026-10-17-001-ci-postcheck.md)。
- **私有真实样本新口径复测（2026-10-18）**：同一 SHA-256 的 10 股 BaoStock 快照在临时内存库中完成动量／反转预设验证期、严格交集、观测产物计数及 CSV/HTML 核对；验证期共同有效 IC 日 58、严格交集 580 条，证据等级仅 `limited`。后端 209 项与黄金验算通过；未重新联网采集、未做真实数据浏览器导出或 Windows 验收。见 [CHG-20261018-004](changes/2026-10-18-004-real-sample-validation-comparison.md)。

- **本机基线（2026-10-15，提交 `fffad78`）**：`.venv/bin/python -m unittest discover -s backend/tests -q` 152 项通过；`.venv/bin/python tools/verify_golden_research.py` 通过；`npm run build --prefix frontend` 通过。此后权重校验变更再次运行后端 152 项与黄金样例，结果均通过，见 [CHG-20261015-014](changes/2026-10-15-014-composite-weight-validation.md)；未重新运行前端构建，因本次未改前端。
- **CSV 快照修正本机工作树（2026-10-15）**：后端 155 项和黄金样例通过，详见 [CHG-20261015-016](changes/2026-10-15-016-verified-csv-snapshot.md)；本次未改前端，未重复构建。提交后 CI 仍须另查。
- **历史包加载修正本机工作树（2026-10-15）**：后端 156 项、黄金样例与本机私有包只读加载通过；加载得到 292 个日历日、242 个成员日、328 只证券、95,776 条行情，见 [CHG-20261015-017](changes/2026-10-15-017-historical-load-snapshot.md)。本次未重新运行浏览器任务或 Windows 部署。
- **历史包修正后隔离 API 复测（2026-10-15）**：内存 SQLite 与临时报告目录中新建真实私有包 inline 任务并通过 HTTP 下载四份产物，独立核对 72,366 个有效观测、968 行逐日审计、32 条无标签信号及 HTML 摘要，见 [CHG-20261015-018](changes/2026-10-15-018-historical-inline-api-qa.md)。不是 Celery/Compose 或浏览器验收。
- **普通 CSV 缺行修正本机工作树（2026-10-15）**：后端 158 项及黄金样例通过；同一 SHA-256 的私有 10 股小样本五因子观测/日期数与既有记录一致。缺行合成案例见 [CHG-20261015-019](changes/2026-10-15-019-csv-calendar-continuity.md)；本次未重跑真实样本 API/Worker 或浏览器。
- **CSV 质量提示本机工作树（2026-10-15）**：后端 159 项、黄金样例与前端生产构建通过；本机同一私有 10 股样本报告 117 个推断市场日、0 个内部断档，见 [CHG-20261015-020](changes/2026-10-15-020-csv-internal-gap-quality.md)。尚未执行真实浏览器交互验收。
- **全数据集日历修正本机工作树（2026-10-15）**：后端 161 项和黄金样例通过；API 合成缺行案例验证仅选 A/B 时未选 C 仍提供日历，真实 10 股 CSV 中选 2 股得到动量 192/96、PE 232/116（观测/日期），见 [CHG-20261015-021](changes/2026-10-15-021-full-dataset-calendar.md)。未重跑真实浏览器或容器队列。
- **内置演示种入一致性本机工作树（2026-10-15）**：后端 162 项与黄金样例通过；全新 `demo_daily` 的质量报告及摘要使用同一字节快照，见 [CHG-20261015-022](changes/2026-10-15-022-demo-seed-byte-consistency.md)。未改前端或现有演示库。

- 本机虚拟环境：`130` 项后端测试通过；黄金结果脚本在 `PYTHONIOENCODING=cp1252` 下通过；前端生产构建通过。历史采集测试曾在模拟“未安装 BaoStock”条件下 `129` 项通过，见 [CHG-20261014-018](changes/2026-10-14-018-optional-baostock-test-isolation.md)。
- GitHub Actions：提交 `8ab9252` 的 [运行 #38538602151](https://github.com/cangshan-cloud/PBL/actions/runs/38538602151) 在 Ubuntu、Windows 后端测试均失败。测试隔离修复 `08e512b` 的 [运行 #38539572865](https://github.com/cangshan-cloud/PBL/actions/runs/38539572865) 让 Ubuntu 全部成功，Windows 仍失败；显式 UTF-8 修复 `2c5698f` 的 [运行 #38540261543](https://github.com/cangshan-cloud/PBL/actions/runs/38540261543) 使 Windows 后端测试通过，失败点转到黄金验算。`PYTHONIOENCODING=cp1252` 在本机复现了中文成功提示的 `UnicodeEncodeError`；改为 ASCII 并加回归后，提交 `c376d4a` 的 [运行 #38540761105](https://github.com/cangshan-cloud/PBL/actions/runs/38540761105) 公开页面显示整条工作流 **Success**（Ubuntu、Windows 矩阵均完成）。
- 后续代码提交 `54b86f6`、`0a7c453`、`fffad78`、`a1e64d1` 的 GitHub Actions 运行均显示成功。最近的 `11e0ce9` 对应 [运行 #38742778282](https://github.com/cangshan-cloud/PBL/actions/runs/38742778282)，公开作业接口显示 Ubuntu 与 Windows 两个 `Verify` 作业均为 `completed/success`（2026-10-15 核对）。这只证明工作流所含单元测试、黄金验算与前端构建；不能代替 Windows Docker/WSL2 离线部署和浏览器验收。本次文档提交及更晚提交须另查其自身 CI。

## 下一步顺序与放行门槛

2026-10-28 后续增量：[历史固定 7 月切分](HISTORICAL_FIXED_SPLIT_QA_2026-10-28.md)已在隔离私有封存包新 Run 上完成任务、报告、V2 复现和 242 日结果一致性核对；前端单测与生产构建通过。此记录补充下面原有基线顺序，不把旧条目在当时的测试数和状态改写为当前状态；主 Compose 页面尚未重建实点。

2026-10-29 后续验收：[固定切分真实浏览器与 Celery 记录](HISTORICAL_SPLIT_BROWSER_QA_2026-10-29.md)补上上一段未覆盖的页面实点，新 Run 的任务、报告与 V2 HTTP 结果核对通过。主 `fbl` 未升级或操作；队长本人仍待亲自产品实测。

1. **逐提交核对 CI**：最近代码提交 `11e0ce9` 的 Ubuntu/Windows 作业均已成功；后续每个新提交仍须核对自己的运行，不沿用前一版本的结果。CI 不覆盖 Compose 和浏览器验收。
2. **固定课程演示范围并完成彩排**：使用固定演示 CSV 跑登录→已发布版本→异步研究→图表／报告→只读权限；按 [`FINAL_REHEARSAL_CHECKLIST.md`](FINAL_REHEARSAL_CHECKLIST.md) 留下提交号、时间、任务 ID、截图与失败收束证据。历史私有包作为有条件扩展，不依赖现场联网采集。演示词区分“软件检验”和“投资结论”。
3. **持续更新四责任包证据**：每轮测试同步记录 A 的集成、B 的数据、C 的公式指标、D 的产品出口；写明实际执行者和未覆盖项。队长后续自行产品实测时补入 D 的用例、缺陷和时长。25% 是计划责任包，不代表可由代执行证明四人已完成等量个人工作。
4. **课程决策点**：确认导师是否要求 Parquet/DuckDB、中性化或服务端 PDF。如果没有明确评分要求，以按时完成可复现闭环为先，更新 PRD 偏差说明；若有，则先做数据与测试设计，再排实现，不隐瞒缺口。
5. **后续环境**：可用 Windows 时补离线 Compose 与浏览器全流程；在此之前保持“Mac 已验、Windows 未验”的表述。
