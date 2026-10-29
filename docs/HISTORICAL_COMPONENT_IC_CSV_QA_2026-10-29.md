# 成分同样本 IC 原值 CSV 导出验收（2026-10-29）

实际执行者：Codex。使用 Mac/OrbStack 隔离五服务和研究员浏览器会话，在任务中心选择已保存的新 Run `9bbb1f11-548d-423c-a56c-ced6eb70d545`，实际点击“下载成分 IC CSV”。浏览器生成 `component-ic-9bbb1f11.csv`；文件位于 Git 忽略的 Playwright 目录，不随项目提交。

文件采用 UTF-8 BOM、CRLF、完整 Run ID，列为 `run_id,factor,ic_mean,rank_ic_mean,valid_ic_dates,signal_date_count,common_coverage`。实际下载内容有四个因子，均为 `242/242`，共同样本 72,366 条；IC/Rank IC 保留原始数值而非页面四位小数。例如动量 `0.008943096712500317 / 0.000512273381447914`，反转 `-0.01124131024999272 / -0.0013148344186104377`，与先前[真实样本验收](HISTORICAL_COMPONENT_IC_QA_2026-10-29.md)相符。

切换旧 Run `1af438dd-8583-4525-b1ad-66dca0ff8043` 后，页面显示“此归档任务未保存成分 IC 诊断。”且没有成分 CSV 下载按钮；不会导出空表冒充旧计算结果。浏览器控制台 0 error、0 warning。

前端 88 项测试和生产构建通过。自动测试还覆盖空指标单元格、负数原值、完整 Run 身份与文本单元格公式防护。此次不改变后端计算、数据包或归档报告，未重跑后端测试；队长本人实测和来源授权核验仍未进行。隔离项目验收后 `down` 且不删卷，主 `fbl` 仍 `running(5)`。
