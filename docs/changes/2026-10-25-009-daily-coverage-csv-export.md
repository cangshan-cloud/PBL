# CHG-20261025-009 全量逐日诊断 CSV 导出

## 问题与决策

前一轮逐日表仅可分页和筛选。普通研究模式缺少便于研究员离线逐日核对的表格出口；历史模式的因子级审计 CSV 与汇总逐日诊断不是同一口径。决定由浏览器基于当前已取回的 `daily_coverage` 生成全量诊断 CSV，固定原始顺序，不让页面筛选改变下载内容。CSV 带 Run ID 和原始状态码，不推断停牌原因；不冒充服务端归档、复现包或可成交回测。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/daily-coverage-export.ts::dailyCoverageCsv`、`dailyCoverageFilename`：全量 CSV、UTF-8 BOM、空值、CRLF、字段转义及电子表格公式注入防护。
- `frontend/src/DailyCoverageTable.tsx::DailyCoverageTable`：独立下载按钮，始终使用原始 `rows`；提示 CSV 含全部日期。
- `frontend/src/main.tsx`：传入当前 Run ID；`frontend/package.json` 增加测试入口。
- `frontend/tests/daily-coverage-export.test.ts`：身份、全量日期、原始数值与空值、转义和公式防护回归。
- `docs/SINGLE_FACTOR_ANALYSIS.md`、变更索引与 A/B/C/D 责任包：记录用途和边界。

## 验证结果与边界

前端 57 项测试及生产构建通过；后端全量回归、黄金核对、变更台账及链接检查见本轮提交。本轮未重新构建容器或实点下载按钮；浏览器下载体验和文件落盘待后续产品实测。导出仍依赖当前任务结果的正确性，不认证市场数据来源或授权。用户修改的分工 Excel 未处理。
