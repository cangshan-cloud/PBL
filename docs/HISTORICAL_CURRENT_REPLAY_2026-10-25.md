# 当前源码历史私有包隔离复算记录（2026-10-25）

## 目的与隔离范围

2026-10-14 留存的旧历史导出不能在当前源码下精确复算，因此本轮用同一个本机私有封存包生成**当前源码的新任务**并核对。`tools/run_isolated_historical_replay.py` 只使用内存 SQLite、临时报告目录和本机封存包；不连接现有 API、Worker、Redis、PostgreSQL 或 OrbStack 主栈。派生的复现 JSON 与报告 HTML 留在 Git 忽略的 `data/real/current_replay_2026-10-24/`，原始行情不进入仓库。实际执行者：Codex；队长本人未做产品实测。

## 执行与结果

输入为私有包 `hs300_2024_0375298bd2c8ac52`，使用冻结的四因子等权、5 组、10 bps 参数。运行命令：

```bash
.venv/bin/python tools/run_isolated_historical_replay.py \
  data/real/bundles/hs300_2024_0375298bd2c8ac52/manifest.json \
  data/real/current_replay_2026-10-24 --acknowledge-private-output
```

隔离任务 ID `3a559947-e620-48f2-b00c-af57473e056f`，四因子共同有效观测 72,366；复现结果 SHA-256 为 `61b3dafbf4ad0eb49e89c9bebfe74a3b335f9aa038d185a76e605c931472e1ec`，报告 SHA-256 为 `2f5888643eee99b9913ea8f17c54a67b95c635ce3b0b651d2eee02d28e776725`。脚本在完成任务后校验两份导出的摘要，并调用当前源码只读复算工具；随后又从落盘文件独立运行两条 CLI，结果均通过：

```bash
.venv/bin/python tools/verify_reproducibility_export.py \
  data/real/current_replay_2026-10-24/reproducibility.json \
  --report-html data/real/current_replay_2026-10-24/report.html
.venv/bin/python tools/verify_historical_recomputation.py \
  data/real/current_replay_2026-10-24/reproducibility.json \
  data/real/bundles/hs300_2024_0375298bd2c8ac52/manifest.json
```

这些文件仅在本机私有目录存在，仓库克隆者不能直接运行上述带数据路径的命令。脚本拒绝已存在的输出目录，要求显式确认，并限制输出在忽略的 `data/real/` 下。

## 解释边界

2026-10-25 后续复核将离线结果比较收紧为严格逐值一致；微小浮点改动即使同步重算导出摘要也会被拒绝。既存当前导出在该严格口径下仍通过。见 [CHG-20261025-002](changes/2026-10-25-002-strict-historical-replay-equality.md)。OrbStack Docker socket 本轮不可用，隔离 Celery/HTTP 验收待恢复。

这证明当前任务代码产生的新结果在**同一份本机私有数据和当前源码**下可重复，且报告字节与归档摘要一致；不等于独立公式验算、市场数据授权认证、官方成分生效时点核验或可成交回测。旧导出与当前口径不一致的事实及其不可变保留，见 [上一轮复算记录](changes/2026-10-24-013-historical-result-recomputation.md)。本轮不是 Celery/OrbStack 或浏览器互动验收；队长本人产品实测仍待完成。
