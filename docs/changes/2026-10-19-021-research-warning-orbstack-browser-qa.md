# CHG-20261019-021 研究页周末提醒的 OrbStack 浏览器验收

## 问题与决策

CHG-20261019-020 已实现并通过前端测试，但当时的本机 Web 容器仍是旧镜像，不能据此声称页面验收。决定只重建、替换现有 Compose 项目的 Web 服务，保留 API、Worker、PostgreSQL、Redis 和数据卷；再在真实浏览器切换所选数据版本核对提醒。实际执行者：Codex。

## 修改位置

- 无新增产品代码改动；部署操作为 `docker compose build web`、`docker compose up -d --no-deps --force-recreate web`。新 Web 镜像 SHA-256：`d2c4d98f613d935b6d7ad6e1afb126506a2eaf2093337c5cd84a349d92dc181f`。
- 页面功能位置：`frontend/src/main.tsx` 研究工作台配置区、`frontend/src/dataset-alerts.ts`。本轮更新 `docs/ORBSTACK_DEPLOYMENT.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包。
- 截图：`outputs/qa-2026-10-19/research-selected-weekend-alert.jpg`、`outputs/qa-2026-10-19/research-selected-clean.jpg`。

## 验证结果

- 更新后 API、Worker、PostgreSQL、Redis 仍健康，Web 运行；仅 Web 容器的创建时间/镜像改变。网页管理员登录成功；概览显示 3 个数据版本、27 个成功任务、27 份报告，与更新前一致。
- 研究工作台默认选中 `compose_accept_20261019 / 20261019.133241.102062` 时，页面展示该版本完整身份及“1 个周末日期、2 行行情”的提醒，并明确不自动删行或禁止运行。切换到 `demo_daily / 0.2.0` 后，所选版本提醒消失；日期输入同步切换到该版本范围。
- Playwright CLI 依赖在本机不可用，按技能回退使用应用内浏览器完成实点。页面操作没有提交新研究任务或改动数据。`git diff --check` 通过。

## 边界

这仅是 Mac/OrbStack 管理员页面验收；未覆盖 Windows、其他角色和移动端视觉。周末日期诊断依旧不能替代交易所日历或数据来源认证。镜像取自当时有未提交改动的工作区，不等于单一 Git 提交。
