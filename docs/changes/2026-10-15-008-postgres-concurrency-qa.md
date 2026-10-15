# CHG-20261015-008：隔离 PostgreSQL 并发回归入口与实测

- 日期：2026-10-15
- 类型：test harness + PostgreSQL QA evidence
- 状态：verified on Mac OrbStack isolated PostgreSQL
- 关联提交：与本记录同次提交

## 背景与决策过程

任务认领、取消和入队失败已使用数据库条件更新，但先前并发回归仅在 SQLite 文件库运行。为验证目标 Compose 所用 PostgreSQL 的实际更新语义，选择让既有持久化测试模块可通过显式环境变量连接**专用 loopback 测试库**，并严格校验驱动、主机、用户与数据库名。不改默认测试；不在现有 `fbl` 主库建表或创建任务。使用已存在的 `postgres:16-alpine` 镜像启动无卷临时容器，完成后停止并自动移除。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| `FACTORLAB_TEST_DATABASE_URL` 显式覆盖和专用库安全校验 | `backend/tests/test_persistence.py::PersistenceTests.setUp` |
| 主库名、远程主机、错误用户和 SQLite URL 的拒绝回归 | `backend/tests/test_persistence.py::TestDatabaseTargetGuard` |
| 说明复测方式与证据边界 | `docs/TASK_EXECUTION.md::PostgreSQL 隔离并发复测` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- 临时容器名称 `factorlab-pg-concurrency-qa-20261015`，镜像 `postgres:16-alpine`，无持久卷；数据库 `factorlab_test_concurrency`，用户 `factorlab_test`。最终复测随机映射端口为 `127.0.0.1:32769`。
- `FACTORLAB_TEST_DATABASE_URL=postgresql+psycopg://factorlab_test:<临时密码>@127.0.0.1:32769/factorlab_test_concurrency .venv/bin/python -m unittest backend.tests.test_persistence -q`：最终代码 15 项通过，包括目标守卫和三类条件更新竞争；此前中间版本在随机端口 32768 的 14 项也通过。
- 默认 `.venv/bin/python -m unittest discover -s backend/tests -q`：147 项通过。
- 测试结束后执行定向 `docker stop factorlab-pg-concurrency-qa-20261015`；`docker ps -a` 确认临时容器已移除，`fbl` 的 API、DB、Redis、Web、Worker 均仍运行，API/DB/Redis/Worker 健康。
- GitHub Actions 公共 API 显示最近六个提交 `1da375b` 至 `a90ce7a` 的工作流均为 `completed/success`；最新一项：[运行 #38708865518](https://github.com/cangshan-cloud/PBL/actions/runs/38708865518)。

## 风险与未决事项

这组测试是真 PostgreSQL、但仍是单机少量并发，不测 Redis 实际重复投递或 Worker 进程崩溃。`FACTORLAB_TEST_DATABASE_URL` 指定的专用库会被测试写入表和任务，使用前必须确认是一次性隔离数据库。Windows Docker/WSL2 部署验收仍未进行。
