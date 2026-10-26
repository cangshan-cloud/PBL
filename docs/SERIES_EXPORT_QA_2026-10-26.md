# 每日序列导出离线核对验收（2026-10-26）

在 Mac 的 `factorlab-historical-qa-20261025` 专用隔离项目，只启动 DB、Redis、API，使用已有成功 Run `f424f62b-4081-400c-89ef-79bbff4a4e59`。复现 JSON 由隔离 API 只读下载到忽略的 `.playwright-cli/`；IC 和多空 CSV 是前两轮浏览器实际下载的文件。未创建新任务、未改私有包或主 `fbl` 栈。实际执行者：Codex。

执行 `tools/verify_series_exports.py` 同时传入三个文件，得到 `ic_rows=242`、`long_short_rows=242`，原日期顺序、完整 Run、空 IC、毛/净收益、换手、成本、净值及 10 bps 参数逐值一致。单测另覆盖错 Run、缺行、换序、改动指标/成本、列模式改变、NaN、复现结果校验和不符、重复 JSON 键和空序列。本轮结束后隔离容器关闭、卷保留；下载与私有衍生文件不入库。

边界：核对的是三个已有文件相互一致，不是对真实市场数据或收益的独立认证；`result_sha256` 不是外部签名，且不覆盖 `task.id`。队长本人产品实测仍待完成。
