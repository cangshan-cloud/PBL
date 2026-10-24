# CHG-20261022-004 隔离 Celery 来源状态链路验收

## 问题与决策

CHG-003 的接口闭环使用进程内 SQLite 与 inline 执行，尚不能证明最新代码经真实 PostgreSQL/Redis/Celery 容器传递适配元数据。决定只在新建的 Mac OrbStack 隔离 Compose 项目做合成数据验收；先运行只读配置预检，不启动 Web、不触碰主栈。实际执行者：Codex。

## 修改内容与位置

- `docs/MAC_ISOLATED_PRICE_STATUS_2026-10-22.md`：记录隔离项目、预检、数据版本/Run 身份、报告摘要、收尾与限制。
- `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`：更新报告链路的 Mac 容器证据边界。
- `docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：索引本次实际验收和各自限制。本轮无应用代码改动。

## 验证与边界

预检 PASS；隔离 DB/Redis/API/Worker 均健康；合成数据经适配导入发布及 Celery Worker 产生成功报告。原归档 SHA 与索引、交付响应头一致，来源状态在两个出口可见，交付后归档字节不变。精确项目 `down` 完成，容器/网络移除，未用 `-v`，专用卷及运行目录保留。详见 [验收记录](../MAC_ISOLATED_PRICE_STATUS_2026-10-22.md)。这不是浏览器验收、真实财务时点证明或 Windows 验收。
