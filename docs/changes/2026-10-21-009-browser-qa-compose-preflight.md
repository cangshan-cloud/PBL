# CHG-20261021-009 隔离浏览器栈启动前边界预检

## 问题与决策

上一轮人工检查 Compose 合并配置虽能证明当次隔离，但复跑时可能忘记 `-p`、把运行目录指向主栈或误改挂载/端口。决定添加只读预检命令，启动前从 Docker Compose 自身解析后的 JSON 验证边界；仅验证配置，不启动、停止或清理容器。运行目录限已存在的系统临时目录下 `factorlab-browser-qa-*` 专用文件夹。实际执行者：Codex。

## 修改内容与位置

- `tools/verify_browser_qa_compose.py`：检查项目名和网络/数据库卷命名、五服务、独立本机端口、Web API 地址与 CORS、API/Worker 仅有只读样本和隔离运行目录挂载、PostgreSQL 实际挂载及本地 DB/Redis 地址。
- `backend/tests/test_browser_qa_compose.py`：独立项目正例，以及主项目名、非专用目录、额外挂载、端口、样本读写、CORS、数据库卷与 Worker 外部数据库反例。
- `docker-compose.browser-qa.yml`：提示先执行预检。
- `docs/ORBSTACK_DEPLOYMENT.md`、`docs/DEVELOPMENT_PLAN_2026-10-21.md`、总索引及 A/B/C/D 责任包：记录使用方法、证据和边界。

## 验证与边界

预检对上轮保留的精确隔离项目配置返回 PASS，不启动服务；后端全量 **249 passed**，一条第三方弃用警告。首次预检发现 macOS `tempfile.gettempdir()` 不固定为 `/private/tmp`，故允许系统临时目录或 `/private/tmp` 下的专用命名目录，仍拒绝仓库内、主栈和广泛目录。此工具只保证**传入的合并配置**符合约定，不能代替运行时健康检查、浏览器验收，也不保证操作员随后使用相同参数启动。Windows 未验证。
