# 历史固定切分真实浏览器与 Celery 验收（2026-10-29）

实际执行者：Codex；队长与其他组员尚未人工签收。复用已预检的 `factorlab-historical-qa-20261025` 专用 Compose 项目、独立 PostgreSQL 卷、`/private/tmp/factorlab-historical-qa-JYdB72` 运行目录、仅绑定 `127.0.0.1:15122/18022` 的 Web/API。五服务以本轮源码重建；主 `fbl` 项目未操作。

Playwright CLI 命名会话 `historical-split-20261029` 以隔离研究员登录，从研究工作台切换到“2024 沪深300历史研究”。新“研究期／验证期 IC”复选框默认未选，说明固定从 2024-07-01 验证、隔离此前最后一个信号日，全年分组和多空结果不变。勾选并实点“运行研究”，隔离 Worker 完成新 Run `1af438dd-8583-4525-b1ad-66dca0ff8043`。任务中心保存参数含 `validation_start_date=2024-07-01`；规则结论版本 `1.0.3` 以验证期 IC 为标题与分档依据。

研究工作台显示全区间 72,366 条观测、IC 均值 `-0.0314`，新增分段表显示研究期 2024-01-02 至 2024-06-27 的 34,774 条/116 个有效 IC 日，隔离 2024-06-28，验证期 2024-07-01 至 2024-12-31 的 37,292 条/125 个有效 IC 日。每日 IC 图同时标明分段范围，仍保留全区间曲线。报告中心“查看同 Run 报告”绑定完整 Run ID，iframe 归档包含“时间切分 IC 诊断”和相同边界、计数与非前瞻披露。

取消勾选后，当前已完成 Run 的结果和切分表立即隐藏，显示“尚无当前配置的分组结果”；没有把带切分结果冒充未切分配置。640 CSS px 视口截图保存在 Git 忽略的 `output/playwright/historical-split-20261029/.playwright-cli/`，表单及开关可见，`body.scrollWidth=innerWidth=640`；控制台 0 error、0 warning。截图及页面快照不入 Git。

对新 Run 使用只读 HTTP 严格 V2 工具核对复现 JSON、HTML 报告及 242 日结果审计，整包/结果/报告均通过；`result_sha256=94c5b00dc1965fd690c311c813d9c15484a6628cfdb24212e8e934bffe89bc00`，`report_sha256=45f9d192d30f9fe5d0b8b60f02efcf5df7707ab10b71605d802740a5c15e08d0`，`bundle_sha256=e03f1fe1ec952e4442bd649d3bc49d04978a8e3edcfb3a53b31dd3e8e5e68816`。浏览器会话已关闭，仅隔离 Compose 项目执行 `down` 且未使用 `-v`；随后 `docker compose ls` 只显示主 `fbl` 五服务运行。

本轮确认 Mac/OrbStack 上新控件到 Celery、结果、报告和严格 V2 导出的实际路径；不认证原始行情授权、真实可成交收益、Windows 环境或队长本人产品实测。固定切分属于回溯诊断，不能当成前瞻样本外证明。
