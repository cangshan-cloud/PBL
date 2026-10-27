# CHG-20261027-002 打印报告明确逐日明细未包含

## 问题与决策

对新报告做浏览器 PDF 复验发现，逐日核对表默认折叠，打印版只出现表格标题而不含明细；这会使打印报告的证据边界不清。决定保留网页版可展开表格，打印版则用醒目但简短的说明代替折叠控件，列出已知日期数并指向同 Run HTML、逐日 CSV 和复现包。不强制打印数百行宽表，以免课程报告页数失控；若要完整逐日数值，仍以电子结果和导出文件核对。实际执行者：Codex。

## 修改内容与对应位置

- `backend/app/services/reports.py::_daily_series_detail`：在原交互表格后添加仅打印显示的日期数与明细获取说明；无序列日期时不生成表格或说明。
- `backend/app/services/reports.py::build_report_html`：屏幕隐藏 `.print-series-note`，打印时隐藏 `.series-detail` 并显示说明。
- `backend/tests/test_reports.py`：断言打印说明、日期数和 CSS 规则；网页表格仍保留。
- [打印验收](../REPORT_PRINT_QA_2026-10-27.md)、`docs/SINGLE_FACTOR_ANALYSIS.md`、本索引和 A/B/C/D 四责任包：记录取舍、代码位置与验收边界。

## 验证与未决事项

合成报告六页浏览器 PDF 逐页检查无可见图表/正文裁切，修正后第五页明确提示三日明细未随打印版包含。全量自动化与文档检查见本轮提交。真实任务新报告打印版及队长本人产品实测尚未完成；旧归档不回写，临时 PDF 未入库。
