# CHG-20261014-002：历史沪深 300 私有包 OrbStack 隔离队列验收

- 日期：2026-10-14
- 类型：evidence-only / docs
- 状态：verified
- 关联提交：与本记录同次提交

## 背景与目标

历史数据包的本机与浏览器流程已经验收，但还缺 API、Redis、Celery Worker 在 OrbStack 容器中读取私有包并生成报告的实证。已有 `fbl` Compose 项目正在运行，不能为验收覆盖其容器或数据库。

## 决策过程

考虑直接在既有 `fbl` 项目运行、仅用一次性容器计算、独立 Compose 项目三种方式。一次性容器只能证明数据可读，不能证明排队执行；复用既有项目会污染其研究记录。最终选择 `factorlab-hs300-qa` 隔离项目，独立数据库卷、Redis 与运行目录，同时复用只读用途的仓库私有数据包。未改变项目默认部署结构，也不把私有行情提交到 Git。

## 修改内容与对应位置

无代码改动。

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 增加隔离容器验收事实、边界和安全清理说明 | `docs/ORBSTACK_DEPLOYMENT.md` 的“2026-10-14：历史沪深 300 私有包的隔离容器验收” | 部署者可区分演示数据与历史私有包的验证范围 |
| 登记本次变更 | `docs/CHANGE_INDEX.md` 的变更表 | 保持修改记录可追溯 |

## 验证与结果

- `docker compose build api worker web` 成功；两个新镜像的一次性容器各自加载 `hs300_2024_0375298bd2c8ac52` 并计算 `momentum_20d`，得到相同的 `292 / 242 / 328 / 72366`（行情日／2024 成分交易日／股票数／有效观察数）。
- 隔离项目的 db、redis、api、worker 均健康；历史任务 `f7e564f0-b0bb-471b-aa9c-210cb35f1b0b` 经 `apply_async` 入队，Worker 日志确认 received 与 succeeded（约 6.52 秒），数据库状态 `success`。
- 报告产物通过 `read_verified_report` 完整性校验，长度 43,427 字节；再现性包的 `result_sha256=00f3ce7b81fb09bfc1d22bcef128ffec48e8064462766e6a6b98deefafc5aba8`，`report_sha256=167afbdf98b825539fa15647d2017f80f9d9ac392abeea082a50fcae4ca5c9e9`。
- 本次未重新执行前端浏览器流程和 Windows 测试；既有 `fbl` 项目未重建或迁移数据库。

## 风险、回退与未决事项

私有历史包只在本机存在，其他机器无法直接重放本次验收。Worker 仍以 root 运行，这是现有部署限制，不应据此宣称生产级私域安全。验收用临时数据库和容器可按准确项目名删除；此操作不影响 `fbl` 数据卷。正式共享部署和 Windows 环境仍待独立验证。
