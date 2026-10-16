# CHG-20261016-013：当前五服务浏览器异步闭环

- 日期：2026-10-16
- 类型：full-stack browser QA + four-role evidence
- 状态：verified on Mac；timed presentation and Windows pending
- 关联提交：与本记录同次提交

## 背景与决策过程

上轮分别验证了隔离 inline 浏览器流程和当前版本 Celery API/Worker，但两份证据不是同一任务、同一五服务部署。为了避免误称“完整浏览器异步闭环”，决定另建独立 Compose 项目，包含当前 Web/API/Worker、PostgreSQL/Redis，分配独立 loopback 端口与数据库卷，仅只读挂载演示 CSV。使用 Playwright CLI 技能按页面元素快照操作并保留下载文件，再以 Worker 日志与离线摘要核对同一 Run。该技能要求真实浏览器操作和快照，因此本轮页面证据由其产生；不新增 Playwright 测试规格。按队长约定，同步更新 A/B/C/D 四责任包，但明确实际执行者。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 五服务浏览器技术验收记录 | `docs/FULL_STACK_BROWSER_ACCEPTANCE_2026-10-16.md` | 同一 Run 贯穿页面、Celery、报告和下载证据 |
| A/B/C/D 本轮对应结果 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` | 每个责任包注明代执行与边界 |
| 正式彩排、PRD 状态 | `docs/FINAL_REHEARSAL_CHECKLIST.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` | 区分技术流程和连续口头计时 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可按变更号定位 |

## 验证与结果

- Compose 项目 `factorlab-browser-qa-1016` 的解析配置、五服务状态及 Mac 宿主机 Web/API HTTP 200 已核对；独立端口 `5175/18003`、数据库卷与临时报告目录不指向主 `fbl`。
- Playwright 浏览器创建 Run `4c05d255-32b8-4e92-b89d-8647e3953448`，Worker 日志显示相同完整 ID 的 `received` 和 `succeeded`；任务成功，1,980 有效观测、99 个有效 IC 截面。
- 浏览器报告预览和两份下载成功；`tools/verify_reproducibility_export.py` 独立核对结果与报告摘要通过；查看者只读按钮禁用；控制台 0 错误、0 警告。
- 后端 185 项、黄金样例、私有 10 股回归和前端生产构建通过。`git diff --check` 见提交前检查。
- 精确项目执行 `docker compose down`，仅移除本轮容器与网络，保留专用数据库卷和报告证据；未对主 `fbl` 执行清理。

## 风险、回退与未决事项

下载与页面快照在 Git 忽略目录，仅本机保留。没有对真实市场全样本、Windows、多人并发或十分钟口头演示计时作出通过声明；默认演示数据为合成数据。隔离 Compose 项目的任务记录保留于其专用卷；关闭项目不得误对主 `fbl` 使用 `down -v`。若日后队长提供手工产品验收数据，应补入 D 材料并另记一次变更。
