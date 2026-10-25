# CHG-20261025-006 真实私有包隔离异步验收与配置固化

## 问题与决策

当前源码的真实包正例此前只覆盖内存库 inline 任务；OrbStack 恢复后需要补齐 API→Redis→Celery Worker→导出→离线复算。临时隔离配置第一次因漏挂内置演示 CSV 导致 API 启动失败，说明一次性手工配置易遗漏。决定将三处挂载、独立端口及项目约束固化到仓库配置和只读预检，不改动主 `fbl` 栈。实际执行者：Codex。

## 修改内容与对应位置

- `docker-compose.historical-qa.yml`：独立 API/Web 本机端口、API/Worker 共享临时运行目录、演示 CSV 与私有包只读挂载。
- `tools/verify_historical_qa_compose.py::validate_config`、`main`：启动前核对唯一项目名、专用临时目录、端口、三挂载、CORS、独立数据库卷、网络与队列地址。
- `backend/tests/test_historical_qa_compose.py`：隔离配置正例与主栈端口、可写私有包、少挂载、错误 CORS/卷/队列反例。
- `docs/HISTORICAL_ASYNC_ACCEPTANCE_2026-10-25.md`、`docs/ORBSTACK_DEPLOYMENT.md`、索引与 A/B/C/D 四责任包：命令、失败原因、真实任务证据和限制。

## 验证结果与未决事项

专用项目 `factorlab-historical-qa-20261025` 两条真实包历史任务成功；正式仓库配置下第二条 Run `189a7e0e-16f2-4a9f-894f-e4a167efaf96`，4 因子、968 行逐日审计、32 条无标签信号、5 分组、72,366 共同观测；报告摘要与私有包同源复算均通过。配置预检及 3 项定向安全测试通过。全量回归、台账与链接结果见本轮提交。主栈五服务仍运行，未操作其数据卷。私有行情及派生文件均被 Git 忽略，用户修改的分工 Excel 未处理。此验收不等于独立公式、数据许可、Windows、浏览器或投资收益证明；队长本人产品实测仍待完成。
专用项目验收后执行 `down`（不加 `-v`）；隔离容器及网络已移除，专用数据库卷和私有证据保留。主栈五服务继续运行。
