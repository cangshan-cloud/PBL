# CHG-20261014-012：演示预检增加可选 Celery Worker ping

- 日期：2026-10-14
- 类型：tool + tests + documentation
- 状态：implemented / verified on macOS OrbStack
- 关联提交：与本记录同次提交

## 背景与目标

演示前只读预检已覆盖页面、API、账号与数据文件，但 Worker 即使离线也会通过。现场第一个研究任务可能因此失败。需要在不创建任务的前提下增加一个可选队列消费者探测。

## 决策过程

使用现有 Compose Worker 容器运行 Celery `inspect ping`，不增加服务端 API 或数据库写入。仅用户显式指定 `--check-worker` 时运行，避免非 Docker 开发模式被误判失败；可通过 `--compose-project` 指向准确的隔离或主项目。要求命令退出码为 0，且输出有独立一行 `pong`，防止“no pong”之类文字被误读。子进程设定 20 秒上限；失败时预检失败关闭。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 可选 Compose Worker ping 与失败关闭、命令行参数 | `tools/check_demo_readiness.py::check_worker`、`main` | 会前可只读验证 Worker 可响应 |
| 正常、错误输出、Docker 缺失及项目定向测试 | `backend/tests/test_demo_readiness.py::DemoReadinessTests` | 防止虚假通过和错误目标 |
| 更新彩排命令与证据边界 | `docs/DEMO_REHEARSAL.md` 的“会前只读预检” | 区分 ping 与真实任务验收 |
| 登记变更 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `make test`：122 项通过。
- 本机 `fbl` 栈执行 `tools/check_demo_readiness.py --check-worker --compose-project fbl`：前端、三账号、演示数据文件、六因子、查看者列表与 Worker `pong` 全部通过；没有创建新任务。

## 风险、回退与未决事项

Worker ping 不保证任务能读取同一数据挂载、不保证研究计算或报告成功，也不验证浏览器交互。此功能依赖本机 Docker Compose 命令，非容器开发模式应不加该参数。Windows 环境未实测。
