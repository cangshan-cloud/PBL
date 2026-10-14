# PRD—实现—测试证据对照表（2026-10-14）

本表供队长控制范围和第一次汇报使用。逐项对照 [`PRD.md`](PRD.md) V1.0，区分“代码存在”“本机验证”“目标环境验收”。测试或脚本通过不等于四位成员已各自签名验收，也不等于研究结论有效。核对截至 2026-10-14 的当前工作树；本机为 macOS，Windows 部署目前不在本轮执行范围。

状态：**已验（Mac）**＝有本机自动测试或实测证据；**部分**＝流程存在但 PRD 口径尚缺项；**未验**＝尚无目标环境实测；**未实现**＝没有相应功能。私有真实行情包在 Git 忽略目录中，不能把仓库代码误称为“任意电脑开箱复现真实样本”。

## 功能与验收矩阵

| PRD 条款与验收点 | 当前状态 | 实现位置与现有证据 | 剩余工作／放行条件 |
| --- | --- | --- | --- |
| §3、§5.1：登录、三角色、后端资源权限 | 已验（Mac） | `backend/app/auth.py`、`backend/app/main.py` 登录与权限路由；`backend/tests/test_auth.py`、`test_api_journey.py` | B/C/D 人员自行按角色完成手工验收；Windows 暂缓 |
| §5.2：CSV 导入、质量校验、SHA-256、发布不可变版本 | 已验（Mac） | `backend/app/services/datasets.py`；`backend/tests/test_datasets.py`、`test_versioning.py`、`test_storage_audit.py`；[`DATASET_FORMAT.md`](DATASET_FORMAT.md) | B 提交来源、字段、异常样本和签名导入记录 |
| §4、§5.2、§7：Parquet 导入及 DuckDB/Parquet 大数据存储 | 未实现 | 当前入口为 CSV；PostgreSQL 存元数据，历史包为封存 CSV；[`PROJECT_STATUS_2026-10-12.md`](PROJECT_STATUS_2026-10-12.md) 已列为缺口 | 属 PRD 与当前实现的显式偏差；在课程评分要求确认前不扩大范围，最终需修订 PRD 或实现并实测 |
| §5.2：证券主表、日历、复权、行业历史、基准行情与财务披露时点 | 部分 | CSV 字段和价格口径见 [`DATASET_FORMAT.md`](DATASET_FORMAT.md)、[`PRICE_BASIS.md`](PRICE_BASIS.md)；历史包含日历、成员、行情、交易/ST 状态 | 行业历史、完整基准和财务公告时点未形成通用数据链路；不得宣称财务无前视偏差 |
| §5.3：六个版本化内置因子 | 已验（Mac），真实样本有限制 | `backend/app/domain/factors.py::FACTOR_REGISTRY`、`backend/app/services/catalog.py`；`backend/tests/test_factors.py` | 演示 CSV 可覆盖六因子；真实 BaoStock 样本不含总市值，2024 历史包仅跑四个价格/换手率因子；C 需明确解释差异 |
| §5.4：样本／日期选择、MAD 去极值、Z-score、异步任务 | 已验（Mac） | `backend/app/services/runs.py`、`backend/app/tasks.py`、`backend/app/domain/research.py`；`backend/tests/test_research.py`、`test_api_journey.py` | 把参数和任务结果纳入 D 的完整剧本实测 |
| §5.4：行业与市值中性化 | 未实现 | [`SINGLE_FACTOR_ANALYSIS.md`](SINGLE_FACTOR_ANALYSIS.md) 记录边界 | 保持为缺口；若导师明确要求，先取得行业/市值时点数据及黄金结果，再评估实现量 |
| §5.4：进度、日志、取消、失败重试 | 已验（Mac） | `backend/app/main.py` 任务路由、`backend/app/services/runs.py`；`backend/tests/test_persistence.py`、`test_api_journey.py`；[`TASK_EXECUTION.md`](TASK_EXECUTION.md) | D 用失败/取消样例记录界面验收证据 |
| §5.5：IC、Rank IC、ICIR、分组／多空净值、换手率、成本口径 | 已验（Mac），非实盘回测 | `backend/app/domain/research.py`；`backend/tests/test_research.py`；[`GOLDEN_RESEARCH_VERIFICATION.md`](GOLDEN_RESEARCH_VERIFICATION.md)；[`SINGLE_FACTOR_ANALYSIS.md`](SINGLE_FACTOR_ANALYSIS.md) | C 亲自独立复核至少一组黄金指标并署名；不得把统计检验等同于可成交收益 |
| §5.5、P1：历史沪深 300 成分与停牌/ST 可交易性 | 已验（Mac 私有包），来源边界未消除 | `backend/app/domain/historical_research.py`、`backend/app/services/historical_bundle.py`；[`HS300_BUNDLE.md`](HS300_BUNDLE.md)、[`INDEPENDENT_HS300_SPOTCHECK.md`](INDEPENDENT_HS300_SPOTCHECK.md) | 封存包需另行取得；成分生效时点、ST 源状态未全量独立核验；C/B 分别签收公式与来源证据 |
| P1：等权多因子及相关矩阵 | 已验（Mac） | `backend/app/domain/composite.py`、`backend/tests/test_composite.py`；[`MULTI_FACTOR_ANALYSIS.md`](MULTI_FACTOR_ANALYSIS.md) | IC 加权未实现；按已确认的课程范围保留等权，不把相关性解释为因果或独立增益 |
| §5.6：结构化结果、图表和独立 HTML 报告 | 已验（Mac） | `backend/app/services/reports.py`、`backend/app/services/reproducibility.py`、`frontend/src/main.tsx`；`backend/tests/test_reports.py`、`test_reproducibility.py` | D 用实际浏览器走一遍报告预览、下载和限制说明 |
| §5.6、P1：PDF 导出 | 部分 | 浏览器可打印 HTML 为 PDF；[`README.md`](../README.md) 报告中心说明 | 无服务端 PDF 文件生成接口；答辩时如称“支持 PDF”，须限定为浏览器打印并实测 |
| §9.4：任务复现信息、文件和结果摘要 | 已验（Mac），跨机有条件 | `backend/app/services/reproducibility.py`；`backend/tests/test_reproducibility.py`；历史四文件核对见 [`HS300_BUNDLE.md`](HS300_BUNDLE.md) | 复现包不包含原始私有行情及代码副本；跨机复算须另备相同数据和代码 |
| §8：Web/API/Worker/PostgreSQL/Redis 私域 Compose 部署 | 已验（Mac OrbStack） | `docker-compose.yml`、[`ORBSTACK_DEPLOYMENT.md`](ORBSTACK_DEPLOYMENT.md)；隔离队列、报告、四文件验收 | Windows/WSL2 离线部署未验；当前只开放本机端口，不能宣称公网或多人生产级安全 |
| §2.3：300 股 × 3 年单因子完整检验 ≤60 秒 | 已验（单次 Mac 基准），目标环境未验 | [`PERFORMANCE_ACCEPTANCE.md`](PERFORMANCE_ACCEPTANCE.md) 记录完整 Run 1.614 秒、220,500 有效观察 | 需在最终推荐环境重复测量并记录硬件、版本；单次结果非通用性能保证 |
| §2.3：普通页面查询 ≤2 秒 | 未验 | 当前无成套页面延迟基准记录 | D/A 明确定义页面和样本量，至少采集 3 次冷/热访问数据 |
| §2.2、§12：10 分钟离线演示与四人独立责任包 | 部分 | [`DEMO_REHEARSAL.md`](DEMO_REHEARSAL.md) 有剧本与只读预检；[`TEAM_PLAN.md`](TEAM_PLAN.md) 有四包划分 | D 亲自彩排并记录实际耗时；A/B/C/D 分别填写 `docs/member-deliverables/` 的署名验收材料，不能以模板代替贡献 |
| §5.7：Ollama 摘要；P2 表达式编辑器 | 未实现，非首期放行项 | [`PRD.md`](PRD.md) 已列 P2 | P0 缺口和验收证据收齐前不启动 |

## 自动化与环境证据

- 本机虚拟环境：`130` 项后端测试通过；黄金结果脚本在 `PYTHONIOENCODING=cp1252` 下通过；前端生产构建通过。历史采集测试曾在模拟“未安装 BaoStock”条件下 `129` 项通过，见 [CHG-20261014-018](changes/2026-10-14-018-optional-baostock-test-isolation.md)。
- GitHub Actions：提交 `8ab9252` 的 [运行 #38538602151](https://github.com/cangshan-cloud/PBL/actions/runs/38538602151) 在 Ubuntu、Windows 后端测试均失败。测试隔离修复 `08e512b` 的 [运行 #38539572865](https://github.com/cangshan-cloud/PBL/actions/runs/38539572865) 让 Ubuntu 全部成功，Windows 仍失败；显式 UTF-8 修复 `2c5698f` 的 [运行 #38540261543](https://github.com/cangshan-cloud/PBL/actions/runs/38540261543) 使 Windows 后端测试通过，失败点转到黄金验算。`PYTHONIOENCODING=cp1252` 在本机复现了中文成功提示的 `UnicodeEncodeError`；改为 ASCII 并加回归后，提交 `c376d4a` 的 [运行 #38540761105](https://github.com/cangshan-cloud/PBL/actions/runs/38540761105) 公开页面显示整条工作流 **Success**（Ubuntu、Windows 矩阵均完成）。
- CI 的 Windows runner 通过，也只证明工作流所含单元测试、黄金验算与前端构建；不能代替 Windows Docker/WSL2 离线部署和浏览器验收。

## 下一步顺序与放行门槛

1. **保持 CI 绿色**：代码基线 `c376d4a` 的 Ubuntu/Windows CI 已成功；后续每次修改继续检查新运行。CI 不覆盖 Compose 和浏览器验收。
2. **冻结第一次汇报可演示范围**：使用固定演示 CSV 跑登录→发布版本→异步研究→图表／报告→只读权限；历史私有包作为有条件扩展证据，不依赖现场联网采集。演示词区分“软件检验”和“投资结论”。
3. **补真实个人验收**：B 填来源和质量，C 填公式和独立验算，D 填剧本耗时、缺陷和页面检查，A 填部署与集成；各自署名、自测并交叉检查。这里的 25% 是责任包约定，不代表凭现有代码可证明四人已完成等量工作。
4. **课程决策点**：确认导师是否要求 Parquet/DuckDB、中性化或服务端 PDF。如果没有明确评分要求，以按时完成可复现闭环为先，更新 PRD 偏差说明；若有，则先做数据与测试设计，再排实现，不隐瞒缺口。
5. **后续环境**：可用 Windows 时补离线 Compose 与浏览器全流程；在此之前保持“Mac 已验、Windows 未验”的表述。
