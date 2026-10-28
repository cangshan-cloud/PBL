# CHG-20261028-004 新 Celery 历史任务严格 V2 验收

## 问题与决策

前两轮 V2 证据分别来自本机内存任务和隔离 API 对旧成功 Run 的只读动态导出，尚未覆盖新版 API/Worker 从新任务到四文件下载的全链路。决定在独立 QA 项目上新建真实历史包任务，并让验收脚本显式要求 V2；旧脚本默认兼容 V1，避免破坏留存旧环境的用法。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_historical_api_journey.py::run_journey`、`main`：新增 `--require-v2`，将严格版本要求传给下载包离线核验；其余写入隔离栈与拒绝覆盖保护不变。
- `backend/tests/test_historical_api_journey.py::test_strict_v2_option_reaches_export_verifier`：验证严格选项到达校验器；既有创建/发布/下载回归保持。
- `docs/V2_HISTORICAL_CELERY_QA_2026-10-28.md`、`docs/HISTORICAL_ASYNC_ACCEPTANCE_2026-10-25.md`、`docs/REPRODUCIBILITY_EXPORT_CHECK.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：命令、结果、限制与索引。

## 验证与未决事项

隔离 Compose 预检通过；新 Celery Run 成功，严格 V2 JSON/HTML 与两份历史审计 CSV 通过，私有包同代码复算及保存结果内部审计通过。后端全量 315 项和黄金研究样例通过。QA 容器已关闭但独立卷保留；主 `fbl` 未改，仍可能导出 V1。无浏览器点击或队长人工验收，结果不代表独立公式/行情授权或投资收益证明。
