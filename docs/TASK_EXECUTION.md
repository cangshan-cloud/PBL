# 任务执行、取消与日志

## 1. 状态机

研究任务使用以下状态：

```text
pending ──→ running ──→ success
   │           ├──────→ failed
   │           └──────→ cancelled
   ├──────→ failed（入队连接失败）
   └──────→ cancelled
```

成功、失败和已取消均为终态，终态任务不能再次改变状态。需要重新运行时，系统创建新的实验和 Run，原记录保持不变。

Celery 模式下，如果 API 在创建数据库任务后遇到可识别的消息队列连接错误，只能用条件更新把**仍为 `pending`** 的 Run 标为 `failed`，保存固定错误日志并返回 503；队列恢复后可重试。若 Worker 已认领或状态已变化，API 不会覆盖它，而是返回“先检查任务状态，避免重复提交”的 503。错误响应与任务日志不包含底层 Redis 异常文本。数据库与 Redis 投递仍非原子事务，不能仅凭一次 HTTP 503 判断消息绝未送达。

Worker 收到延迟或重复消息时，通过数据库条件更新 `pending → running` 认领 Run；只有更新到一行的 Worker 进入计算并写入一条 `started` 日志，其余消息只读取当前状态，不重复写指标或报告。该条件认领覆盖同一 Run 的并发 Worker 竞争，但不等于“恰好完成一次”：Worker 在运行中崩溃仍可能留下 `running`，消息投递与数据库也不是原子事务；需人工核对日志后决定是否新增重试任务。

## 2. 取消语义

- `pending`：接口用数据库条件更新把任务改为 `cancelled`；Celery 模式同时撤销相同任务 ID 的队列消息。若 Worker 已抢先认领，则不覆盖 `running`，转为运行中取消请求。
- `running`：接口用条件更新写入一次取消请求和审计日志，Worker 在数据读取、因子计算、指标计算三个阶段之间检查并安全停止；重复请求不会重复记日志。
- 系统不使用强杀 Worker 的方式取消任务，避免数据库事务或报告文件只写入一半。
- 计算函数当前是同步执行，因此正在进行的单个计算步骤不能在中间打断；最长响应时间取决于该步骤耗时。
- 本地 `inline` 模式会在创建请求内完成计算，主要用于开发；需要演示排队与取消时应使用 Docker Compose 的 Celery 模式。

## 3. 执行日志

每个 Run 保存结构化日志，包含时间、级别、事件代码和中文说明。正常执行通常依次产生：

1. `queued`
2. `started`
3. `dataset_loaded`
4. `factor_calculated`
5. `metrics_calculated`
6. `completed`

失败会产生 `failed`，取消请求和完成取消分别产生 `cancellation_requested`、`cancelled`。日志保存在数据库中，不依赖 Worker 终端输出。

## 4. 接口与权限

| 接口 | 管理员 | 研究员 | 只读用户 |
| --- | --- | --- | --- |
| `GET /research/tasks/{id}/logs` | 全部任务 | 仅本人任务 | 全部任务 |
| `GET /research/tasks/{id}/conclusion` | 全部成功任务 | 仅本人成功任务 | 全部成功任务 |
| `POST /research/tasks/{id}/cancel` | 全部任务 | 仅本人任务 | 禁止 |
| `POST /research/tasks/{id}/retry` | 失败或取消任务 | 仅本人失败或取消任务 | 禁止 |
| `POST /research/comparisons` | 全部成功任务 | 仅本人成功任务 | 全部成功任务 |
| `POST /research/comparisons/export.csv` | 全部成功任务 | 仅本人成功任务 | 全部成功任务 |
| `POST /research/comparisons/export.html` | 全部成功任务 | 仅本人成功任务 | 全部成功任务 |

重试按原任务模式重新创建：普通单因子、多因子等权组合、2024 沪深 300 历史四因子任务分别走各自的数据与参数校验。新任务会生成新的实验、Run ID、排队时间和日志，原任务状态与结果保持不变。若原数据版本已不再满足发布条件，接口返回可解释的 400/404，而不是创建错误模式的任务；历史私有包文件完整性仍在实际执行时验证。

2026-10-16 增加隔离 HTTP 验收：在 Celery 入队函数被 mock、不会接触真实队列的 SQLite 测试中，研究员创建 `pending` 任务后，查看者及其他研究员的取消／重试均被拒绝；本人取消得到 `cancelled`、`queued → cancelled` 日志和一次非强制撤销调用。重复取消返回 409；重试产生新 ID 的 `pending` 任务且参数保持一致，原任务仍为 `cancelled`；对新 `pending` 任务重试返回 409。该证据覆盖接口状态和权限，不证明真实 Worker 撤销及时性或浏览器按钮交互。

## 5. PostgreSQL 隔离并发复测

`backend/tests/test_persistence.py` 默认使用临时 SQLite 文件；设置 `FACTORLAB_TEST_DATABASE_URL` 后，可以把同一组持久化与并发测试运行在独立 PostgreSQL 上。安全校验只接受 loopback 主机、`postgresql+psycopg`、用户 `factorlab_test`、数据库名 `factorlab_test_concurrency`，避免误对项目主库建表。测试会在该专用库建表和写入任务，因此不能把主栈 `factorlab` 数据库 URL 传入。

2026-10-15 在无持久卷的临时 `postgres:16-alpine` 容器运行最终模块，15 项通过，覆盖安全目标守卫、双 Worker 认领、取消/认领和入队失败/认领竞争；测试后已停止并自动移除容器，原 `fbl` 五项服务仍运行。此结果是单机小样本并发回归，不是高并发压力测试，也不验证 Worker 崩溃自动恢复。
