# CHG-20261022-010 Web 容器 HTTP 健康检查

## 问题与决策

API、Worker、数据库和 Redis 原有健康检查，但 Web 在 Compose 中仅显示 `Up`。CHG-009 已证明隔离页面可实际交互；为了后续启动与排障可观察性，给 Web 增加容器内首页 HTTP 检查，并让主配置检查与隔离预检均要求该配置。选择 Node 22 内置 `fetch`，不引入 `curl` 或新依赖。实际执行者：Codex。

## 修改内容与位置

- `docker-compose.yml::services.web.healthcheck`：以 2 秒请求超时检查 `127.0.0.1:5173/` 的成功 HTTP 响应，设启动宽限、重试及间隔。
- `tools/verify_compose_config.py`：五服务均须有健康检查。
- `tools/verify_browser_qa_compose.py`、`backend/tests/test_browser_qa_compose.py`：隔离预检检查 Web 健康配置，并添加缺失反例。
- `docs/ORBSTACK_DEPLOYMENT.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、总索引及 A/B/C/D 四责任包：同步运行证据和边界。

## 验证与边界

隔离预检与主 Compose 配置检查 PASS；隔离预检单元测试 3 项、后端全量 256 项通过。专用 `factorlab-browser-qa-1022-price` 五服务启动后，`docker compose ps --format json` 显示 Web 和其余四服务全部 `healthy`。精确项目已 `down`，未使用 `-v`，专用卷与运行目录保留，主栈未重建或重启。

Web 健康只检查容器内首页，不证明宿主机端口转发、API 业务流程、用户登录或研究结果。若容器内成功而宿主机无法访问，仍须按部署文档独立检查。此轮没有新增任务或数据。
