# CHG-20261026-014 报告增加折叠逐日序列核对表

## 问题与决策

HTML 报告已有逐日曲线，但读者不离开报告就不能核对某个日期的实际展示值，也不易分辨某条曲线的缺日。决定从同 Run 保存的 IC、Rank IC、多空毛／成本后净值、各组净值构造日期并集，增加默认折叠的逐日表。缺值以“—”展示，不补零、不沿用前值；表中统一四位小数，仅供人工核图，完整精度仍依赖结构化结果/CSV。控制默认篇幅和窄屏横向滚动；不改研究计算、API、结果存储或既有归档。实际执行者：Codex。

## 修改内容与对应位置

- `backend/app/services/reports.py::_daily_series_detail`：按保存日期并集连接四类序列，生成空缺明确、日期转义的折叠 HTML 表；无序列时不生成空表。
- `backend/app/services/reports.py::build_report_html`：将表置于曲线之后；同文件报告 CSS 增加折叠区与横向滚动容器。
- `backend/tests/test_reports.py::test_report_daily_series_table_joins_dates_without_filling_values`：核对错位日期、空值、四位小数、空态、恶意日期转义和报告入口。
- `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/REPORT_DAILY_SERIES_TABLE_QA_2026-10-26.md`、本总索引与 A/B/C/D 四责任包：记录口径、浏览器排版和未验边界。

## 验证与未决事项

后端 293 项、前端 80 项、前端构建及黄金样例通过；合成报告桌面/390 px 窄屏 Playwright 实点展开、列与缺值可见，窄屏容器 `overflow-x: auto`。临时 HTTP 服务因无 favicon 返回一次 404，不是报告脚本错误；浏览器和服务已关闭。台账和文档链接检查见本轮提交。未运行新的真实数据任务，未通过容器实点旧/新正式报告，队长本人产品验收仍待完成。既有归档字节不回写；四位小数不能替代精确 CSV 或独立研究复算。
