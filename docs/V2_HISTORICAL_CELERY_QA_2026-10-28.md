# 新历史任务 Celery → HTTP V2 全链路验收（2026-10-28）

## 隔离与执行

实际执行者：Codex；队长本人和其他组员尚未人工签收。复用专用 `factorlab-historical-qa-20261025` Compose 项目、独立 PostgreSQL 卷和运行目录 `/private/tmp/factorlab-historical-qa-JYdB72`，预检确认 API/Web 只绑定 `127.0.0.1:18022/15122`、私有封存包只读挂载。重建并启动 db、redis、api、worker、web；主 `fbl` 五服务未操作。

在独立数据库复用已发布的 `hs300_2024_0375298bd2c8ac52` 数据版本，新建一条 5 组历史研究任务，由 Celery Worker 完成。专用验收脚本使用新 `--require-v2` 选项；四份 HTTP 下载仅存于 Git 忽略的 `data/real/historical_api_v2_20261028/`，不提交行情或结果文件。

```bash
FACTORLAB_HISTORICAL_ADMIN_PASSWORD='<隔离管理员密码>' \
FACTORLAB_HISTORICAL_RESEARCHER_PASSWORD='<隔离研究员密码>' \
.venv/bin/python tools/verify_historical_api_journey.py \
  --api-url http://127.0.0.1:18022/api/v1 \
  --bundle-id hs300_2024_0375298bd2c8ac52 \
  --output-dir data/real/historical_api_v2_20261028 \
  --acknowledge-isolated-writes --require-v2
```

## 结果

新 Run `dc520031-3a62-40d7-ac1e-1fa3e9d1456f` 状态 `success`；4 个因子、5 组、逐日审计 968 行、无标签信号 32 行。下载文件为整型 `schema_version=2`；结果摘要 `61b3dafbf4ad0eb49e89c9bebfe74a3b335f9aa038d185a76e605c931472e1ec`，整包摘要 `d47237152f168784360da50cc286c157ba70a393312af3ae8443d7a12650232f`，HTML 报告摘要 `d183cf52a2f7ac481fd643b8016c85075f4eb71efd53159d03d6a9f56d0463bc`。

严格 V2 离线工具返回结果、整包、报告三项通过；两份审计 CSV 与复现包一致。使用同一本机私有封存包、当前源码只读复算，4 因子、5 组、72,366 条有效观察严格逐值一致。保存结果内部审计返回覆盖/IC/分组日期各 242 日、组收益日期 242、直方图有效 IC 242、有效观察 72,366。另用只读 HTTP 工具对新 Run 再下载，任务身份与三项摘要均通过。

第一次手工复算命令错误地给 `verify_historical_recomputation.py` 传了不支持的 `--report-html`，命令行解析即失败、未执行复算；报告字节已由前一条严格 V2 工具独立核对。去掉错误参数后复算通过，未改服务端或导出文件。

## 收尾与边界

验收后仅对 QA 项目执行 `docker compose down`，不使用 `-v`；独立数据库卷和 Git 忽略的私有验收文件保留供复查。`docker compose ls` 只显示主 `fbl` 五服务仍在运行。本轮确实覆盖新任务的 Celery 执行与 HTTP 导出，但不是浏览器点击、队长人工实测、独立行情来源/授权认证、独立公式验证或可执行收益证明；主栈仍未重建为 V2。
