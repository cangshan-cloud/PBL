# 逐日诊断 CSV 与复现包离线核对（2026-10-27）

对 Git 忽略的旧 Run `f424f62b-4081-400c-89ef-79bbff4a4e59` 留存下载文件执行只读核对，没有启动容器、访问 API、重新下载或创建研究任务。复现 JSON SHA-256 为 `882dbfc9d86d4953991592be13ee2a269d53ef1201363e10a127d74e982133eb`；逐日诊断 CSV SHA-256 为 `c2ea4560a300abfff621a9c43b9c56dc44b6ba4ccf714a0414b5fba7fc8bb2f5`。文件只保留在本机 `.playwright-cli/`，不提交原始或派生私有结果。

执行 `tools/verify_series_exports.py` 同时传入同 Run 的复现 JSON、IC、多空、各组净值及新增诊断 CSV，得到：`ic_rows=242`、`long_short_rows=242`、`group_nav_rows=1210`、`daily_coverage_rows=242`。逐日诊断的固定列、日期顺序、完整 Run ID、可选数值空值、覆盖率和状态码与复现结果逐行吻合。定向反例测试另确认错 Run、删行、改状态、改比例、改表头及空值填零均拒绝。

这是**同源导出一致性检查**，不是数字签名、因子独立复算、市场来源认证或可交易收益证明。旧文件已由此前浏览器验收留存，本轮未重新验证其采集/下载过程；缺少相应本机文件时可按[使用说明](SERIES_EXPORT_VERIFICATION.md)重新从同一成功 Run 下载。
