# A 系统架构与集成验收

## 基本信息

- 负责人：待填写
- 学号：待填写
- 验收日期：待填写
- 对应责任占比：25%

## 交付清单

- [ ] 系统架构说明
- [ ] API与模块清单
- [ ] 数据库迁移记录
- [ ] 异步任务运行记录
- [ ] Docker Compose部署说明
- [ ] 集成测试结果
- [ ] 最终版本发布记录

## 验收记录

填写功能范围、运行环境、验证步骤、实际结果、遗留问题和复核人。

## 历史预填证据（2026-10-16，开发者整理）

| 项目 | 已有证据 | 尚未覆盖 |
| --- | --- | --- |
| 架构与接口 | [`../PRD.md`](../PRD.md)、[`../ORBSTACK_DEPLOYMENT.md`](../ORBSTACK_DEPLOYMENT.md)；Web/API/Worker/PostgreSQL/Redis 分层 | 确认架构图、接口列表与当前提交一致 |
| 数据库与任务 | `backend/app/db.py`、`backend/app/tasks.py`、迁移目录；主栈只读预检 Worker `pong` | 记录正式演示环境迁移版本、API/Worker 镜像版本与一次新建 Celery 任务 ID |
| 集成验证 | [`../DEV_REHEARSAL_2026-10-16.md`](../DEV_REHEARSAL_2026-10-16.md)：隔离 inline 浏览器闭环；后端 182 项、前端构建通过 | 在正式环境重跑并保存原始命令输出；不能用 inline 彩排代替队列验收 |
| 发布 | 当前准备基线 `cd3a262`，彩排材料提交后须换为最终提交号 | 写明最终 commit、CI 链接、部署时间和回退办法 |

上述为上一轮开发者准备材料，不能证明 A 本人曾操作。后续按队长约定由开发者代执行记录，不要求个人签收。

## 2026-10-16 异步链路本轮验收（开发者代执行）

- 执行者：Codex；代码基线 `bebf8fc` + 本轮验收脚本增强。隔离 Compose 项目 `factorlab-async-qa-1016` 的 PostgreSQL、Redis、API、Worker 均健康；迁移 `20261010_0004 (head)`。
- 新任务 `c6f2dc2e-a40a-465e-84ac-31d4fa286716` 经 API→Redis→Celery Worker 执行成功，Worker 日志核对任务 ID；进度 100%，报告目录摘要和复现包结果／报告摘要均通过。主 `fbl` 栈未改动，详见 [`../ASYNC_ACCEPTANCE_2026-10-16.md`](../ASYNC_ACCEPTANCE_2026-10-16.md)。
- 本责任包结论：Mac 隔离异步链路通过；Windows 部署、正式演示镜像及个人操作未验。责任占比仍是计划分工，不表示 A 本人完成该测试。

## 2026-10-16 当前 Web→Celery 浏览器验收（开发者代执行）

代码基线 `2f21021`；独立五服务 Compose、PostgreSQL 卷、loopback 端口和 API CORS 均按合并配置核对。浏览器创建 Run `4c05d255-32b8-4e92-b89d-8647e3953448`，Worker 日志确认接收并完成，报告和复现摘要通过。详见 [`../FULL_STACK_BROWSER_ACCEPTANCE_2026-10-16.md`](../FULL_STACK_BROWSER_ACCEPTANCE_2026-10-16.md)。本轮集成通过；Windows、多人负载与备份恢复未验。实际执行者：Codex。

## 2026-10-16 写入式验收工具防误操作（开发者代执行）

两个 Compose 验收入口现均要求显式目标 URL 和 `--acknowledge-writes`；缺少门槛时单测确认不发网络请求。后端 189 项通过。此项仅加固操作入口，不替代前述 Celery 集成证据；主栈本轮未新增任务。实际执行者：Codex。

## 2026-10-16 固定演示快照预检（开发者代执行）

会前只读检查新增目录摘要固定值，并继续由 API 预览触发文件字节核验。后端 190 项、前端生产构建通过；本轮未连接主栈重做 Celery 集成，不能把预检单测视为队列验收。实际执行者：Codex。

## 2026-10-16 排队取消与重试 HTTP 验收（开发者代执行）

隔离 SQLite 接口测试验证 `pending → cancelled`、日志与一次非强制 Celery 撤销调用，以及重试新建 `pending` 任务；后端 191 项通过。Celery 入队/撤销均由 mock 代替，不能当作真实队列或 Worker 验收。实际执行者：Codex。

