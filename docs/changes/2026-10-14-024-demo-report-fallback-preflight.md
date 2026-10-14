# CHG-20261014-024：演示备用报告的只读完整性预检

- 日期：2026-10-14
- 类型：tool + tests + evidence
- 状态：verified on macOS OrbStack
- 关联提交：与本记录同次提交

## 背景与决策

十分钟演示剧本允许新任务失败时展示同版本旧报告，但原有预检只要求报告列表可访问，不能证明备用报告实际可下载。选择增加**可选** `--require-report-fallback`：要求至少一份成功的 `demo_daily` 0.2.0 任务对应报告能以查看者身份下载，且下载字节的 SHA-256 等于报告目录校验和。默认预检不强制旧报告，以免全新、尚无任务的正常部署被误判为故障。检查保持只读，不创建任务或修改报告。

## 修改内容与代码位置

| 内容 | 位置 |
| --- | --- |
| 增加有 10 MiB 上限的 HTML 报告下载、可选备用报告核验及输出口径 | `tools/check_demo_readiness.py::ApiClient.download_report`、`check_readiness`、`main` |
| 成功、缺失、校验和不符、非 HTML 和超限回归 | `backend/tests/test_demo_readiness.py::DemoReadinessTests` |
| 更新会前命令、说明与实测边界 | `docs/DEMO_REHEARSAL.md::会前只读预检` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：137 项通过。
- Mac OrbStack 现有 `fbl` 栈运行 `tools/check_demo_readiness.py --require-report-fallback --check-worker --compose-project fbl`：前端入口、三账号、演示数据文件、六因子、查看者列表、报告 `4a7c03b3-74d7-4690-8fa8-23a9d6ea1812` 下载及 SHA-256、Celery ping 全部通过；未创建任务。
- 受沙箱限制，本机端口实测需在获准的本地网络权限下运行；非授权的沙箱调用返回 `Operation not permitted`，并非应用故障。

## 风险与未决

“至少一份旧报告可用”不等于新任务执行成功，也不等于浏览器报告展示、全部旧报告或 Windows 环境已通过。10 MiB 只是会前预检下载上限，超限报告会使该可选检查失败，不改变服务端报告接口。成员 D 仍需亲自完成十分钟彩排并提交署名记录。
