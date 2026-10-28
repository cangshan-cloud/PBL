# 既有 Run 的只读 HTTP V2 验收工具（2026-10-28）

## 用法与安全边界

`tools/verify_http_reproducibility.py` 只接受显式 `http://127.0.0.1:<端口>/api/v1` 或 `http://localhost:<端口>/api/v1`，拒绝外部地址、HTTPS、URL 内账号密码、查询参数和跳转。密码只从 `FACTORLAB_HTTP_QA_PASSWORD` 环境变量读取；工具只提交登录请求，其余均为 GET。下载的 JSON/HTML 仅在自动删除的临时目录保存，不写数据库、不新建任务、不保留私有导出。

```bash
FACTORLAB_HTTP_QA_PASSWORD='<隔离研究员密码>' \
  .venv/bin/python tools/verify_http_reproducibility.py \
  --api-url http://127.0.0.1:18022/api/v1 \
  --run-id f424f62b-4081-400c-89ef-79bbff4a4e59 \
  --audit-result
```

命令要求既有 Run 已成功、JSON 必须为 V2、两份响应带附件头。它验证结果、整包及 HTML 原始字节 SHA-256，并把包内 Run ID、状态、参数、数据/因子版本 ID、代码版本及结果与任务 API 响应对齐。`--audit-result` 额外运行保存结果内部算术与日期审计；省略时只验下载及身份绑定。若任一检查失败，非零退出且不输出 token 或密码。

## 本机隔离实测

2026-10-28 用 `factorlab-historical-qa-20261025` 专用 Compose 项目预检后启动 db/redis/api/web，运行上述命令。旧成功 Run `f424f62b-4081-400c-89ef-79bbff4a4e59` 返回 `schema_version=2`；`result_verified`、`bundle_verified`、`report_verified` 均为 `true`。结果摘要 `61b3dafbf4ad0eb49e89c9bebfe74a3b335f9aa038d185a76e605c931472e1ec`、整包摘要 `c1c78be4fbdd70168adfe8ef9c41a6c3c4b613f6f0884347095992ac529abc24`、报告摘要 `0f15657d38f13dd5a2bb68ea4573eb2582847b38ba53d7702141280df6fbcdec`，与前轮人工 HTTP 核对一致。结果审计为 242 个覆盖/IC/分组日和 72,366 条有效观察。

定向测试还覆盖 V1 降级、错误 Run ID、任务参数/结果错绑、报告字节变动、缺附件头及非本机 URL 拒绝。验收后 QA 项目 `down` 且未使用 `-v`，主 `fbl` 五服务仍运行。此处不证明主服务已升级、新任务 Celery 路径、浏览器下载、来源授权或收益真实性。实际执行者：Codex；四名组员均未人工签收。
