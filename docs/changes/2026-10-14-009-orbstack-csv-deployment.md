# CHG-20261014-009：OrbStack 更新与历史审计 CSV 容器验收

- 日期：2026-10-14
- 类型：deployment + evidence-only
- 状态：verified
- 关联提交：与本记录同次提交

## 背景与目标

新审计 CSV 已通过单元和真实浏览器测试，但既有 OrbStack `fbl` 栈仍运行旧镜像。需要把最新代码部署到演示服务，并验证容器中的完整队列和 HTTP 下载链路，同时保留原数据库记录。

## 决策过程

先只读确认数据库迁移是 head、26 条旧任务均成功且没有排队任务，随后只重建 API、Worker、Web，不动 db/redis。主库没有历史任务；为避免写入测试数据，成功下载路径在单独 Compose 项目 `factorlab-hs300-csv-qa` 测试，而主栈仅做健康、端口与演示预检。隔离项目使用独立数据库卷、Redis、运行目录和无宿主机 API 端口；验收后仅清理精确命名的隔离项目。私有行情包不提交 Git。

## 修改内容与对应位置

无代码改动。

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 记录部署范围、容器链路与保留数据边界 | `docs/ORBSTACK_DEPLOYMENT.md` 的“2026-10-14：现有栈更新与审计 CSV 容器验收” | 可区分主栈更新和隔离历史任务证据 |
| 登记本次变更 | `docs/CHANGE_INDEX.md` 的变更表 | 保持修改记录可追溯 |

## 验证与结果

- `docker compose build api worker web` 成功；`up -d --no-deps --force-recreate api worker web` 后五服务正常，API/db/redis/worker 健康，宿主机 API `/health` 和 Web 首页可达。
- 原数据库迁移 `20261010_0004 (head)`；更新前后持久任务数均为 26；`tools/check_demo_readiness.py` 五项检查通过，Worker `inspect ping` 为 `pong`。
- 隔离容器中通过 HTTP 注册、发布私有包，历史任务 `6a006e4a-d513-4f3f-aa21-e103d2cfcf14` 由 Celery 完成。研究员身份下载复现 JSON、逐日和无标签 CSV，三个接口均返回附件；`tools/verify_historical_audit_exports.py` 校验为 4 因子、968 行逐日审计、32 条无标签信号。
- 隔离项目容器、网络、测试数据库卷已删除，主 `fbl` 服务仍运行且任务数保持 26。导出证据暂存 `/private/tmp/fbl-hs300-csv-qa-runtime/csv-qa/`，不属于仓库交付内容。

## 风险、回退与未决事项

主库无历史任务，因此主栈没有执行成功的历史 CSV 请求；成功路径在同版本隔离镜像中验收。私有包只存在于本机，Windows、多人并发、非 root Worker 与共享私域加固仍未验收。若部署回退，应先检查当前任务和数据库状态，不能用 `down -v` 处理主项目。
