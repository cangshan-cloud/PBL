# 任务执行、取消与日志

## 1. 状态机

研究任务使用以下状态：

```text
pending ──→ running ──→ success
   │           ├──────→ failed
   │           └──────→ cancelled
   └──────────────────→ cancelled
```

成功、失败和已取消均为终态，终态任务不能再次改变状态。需要重新运行时，系统创建新的实验和 Run，原记录保持不变。

## 2. 取消语义

- `pending`：接口立即把任务改为 `cancelled`；Celery 模式同时撤销相同任务 ID 的队列消息。
- `running`：接口写入取消请求和审计日志，Worker 在数据读取、因子计算、指标计算三个阶段之间检查并安全停止。
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

重试会复制原实验参数，但生成新的实验、Run ID、排队时间和日志，保证历史结果不可篡改。
