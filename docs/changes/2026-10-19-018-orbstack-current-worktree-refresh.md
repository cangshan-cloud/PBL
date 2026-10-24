# CHG-20261019-018 OrbStack 现有项目应用容器更新

## 问题与决策

Mac 本机 OrbStack 重启后，`fbl` 项目的 `5173/8000` 已恢复，但 API、Worker、Web 容器仍使用约五天前的镜像，不能代表当前工作区近期数据适配、质量提示及研究代码。决定在现有 Compose 项目中只构建并替换 `api`、`worker`、`web` 三个应用服务，不执行 `down`、`down -v`、数据库/Redis 重建或数据卷清理。部署前后读取数据版本数，以发现明显的数据丢失；该计数不等于完整数据库备份或逐行校验。

## 修改位置与环境

- 无应用代码修改；部署命令：`docker compose build api worker web`，随后 `docker compose up -d --no-deps --force-recreate api worker web`。
- `docs/ORBSTACK_DEPLOYMENT.md`：补充这次本机部署验证事实。
- `docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：登记实际执行者、镜像身份、验证和剩余风险。实际执行者：Codex。

部署时仓库 HEAD 为 `fd764d6`，工作区有未提交的项目改动，镜像对应的是当时工作区内容，不是单一已提交版本。应用镜像 SHA-256 前缀：API `0be2c1c5`、Worker `42f416b0`、Web `3acb55c9`。后续代码再变更时须重新构建，不能沿用这条证据。

## 验证与边界

- 更新前 `docker compose config --quiet` 通过；API、DB、Redis、Worker 健康，Web 运行；PostgreSQL 数据版本数为 2。
- 更新后 API、DB、Redis、Worker 健康，Web 运行；DB、Redis 容器未重建，数据版本数仍为 2。
- Mac 宿主机 `http://127.0.0.1:5173/` 返回 200；`http://127.0.0.1:8000/health` 返回 `status: ok`；默认本机演示管理员登录后只读数据列表返回 2 个版本。前端提供的 `src/adapter-upload.ts` 响应包含新“文件已更换”文案。
- `git diff --check` 通过。本轮未重新运行完整因子任务、数据上传或 Windows 验收，也未验证 PostgreSQL 全量行内容/备份完整性。浏览器缓存若仍显示旧 UI，可刷新 `http://localhost:5173/`。
