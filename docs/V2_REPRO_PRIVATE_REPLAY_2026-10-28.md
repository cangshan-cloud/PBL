# V2 复现包：私有历史包隔离复算（2026-10-28）

## 范围与执行

实际执行者：Codex；队长本人和其他成员尚未进行人工签收。本轮输入为本机 Git 忽略的 `data/real/bundles/hs300_2024_0375298bd2c8ac52/manifest.json`，使用 `tools/run_isolated_historical_replay.py` 在内存 SQLite 和临时报告目录生成当前源码的历史任务。派生 JSON/HTML 留在忽略目录 `data/real/replay_v2_20261028/`，未写入 Git；未连接主环境 API、Worker、Redis 或 PostgreSQL。

```bash
.venv/bin/python tools/run_isolated_historical_replay.py \
  data/real/bundles/hs300_2024_0375298bd2c8ac52/manifest.json \
  data/real/replay_v2_20261028 --acknowledge-private-output
.venv/bin/python tools/verify_reproducibility_export.py \
  data/real/replay_v2_20261028/reproducibility.json \
  --report-html data/real/replay_v2_20261028/report.html --require-v2
.venv/bin/python tools/verify_research_result_consistency.py \
  data/real/replay_v2_20261028/reproducibility.json
```

## 结果与限制

隔离 Run `3974f51e-b40e-4bb6-ad9e-fdd2ad68bccc` 成功。四因子、5 组、共同有效观察 72,366；V2 结果摘要 `61b3dafbf4ad0eb49e89c9bebfe74a3b335f9aa038d185a76e605c931472e1ec`，报告摘要 `e026f324bdd7967d627996364856bf618f80068d148d377cc2faba4984b7e804`。严格 V2 核验返回 `result_verified=true`、`bundle_verified=true`、`report_verified=true`。保存结果内部审计返回 242 个日覆盖日期、242 个 IC 日期、242 个分组日期、72,366 条合格观察、242 个分组收益日期和 242 个直方图 IC。

OrbStack 的 Docker socket `/Users/judai/.orbstack/run/docker.sock` 当时不存在，故**没有**完成容器 HTTP 下载或 Celery 验收。上述证据仅证明本机私有数据与当前源码下的离线自洽/同代码复算，不是独立市场数据认证、公式独立验证、签名或可执行收益证明。重新启动 OrbStack 后仍需在隔离项目实测 HTTP V2 下载；不应把本轮结果当作主服务已部署新版。
