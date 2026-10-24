# CHG-20261018-012：对比口径表窄屏可读性与浏览器点测

## 背景与决策

上一轮在“实际研究口径”表新增完整数据版本 ID，留下窄屏呈现未验收的边界。本轮以独立本机栈生成动量、反转两个演示任务，在 640 CSS px 视口核对。发现页面整体不溢出、表格有内部横向滚动，但 ID 仍继承 `white-space:nowrap` 单行显示，且没有文字提示用户横向查看后续口径。决定仅调整该 ID 的换行样式，并在表格标题下加入滚动提示；保持首列固定及原有宽表结构。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 数据版本 ID 单元格允许换行、滚动提示样式 | `frontend/src/layout.css::.comparison-dataset-id`、`.comparison-scroll-hint` |
| 实际研究口径表提示文字 | `frontend/src/main.tsx` 实验对比视图 |
| 本轮记录、总索引、四责任包 | 本文件、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 独立临时 SQLite、API、前端中，研究员运行两条演示任务并生成对比；浏览器确认候选短 ID 和详细表完整 ID。640 CSS px 下 `document.body.scrollWidth == innerWidth == 640`；表格内部 `scrollWidth=1346`、`clientWidth=576`，后续列通过内部横向滚动查看。更改后 ID 的计算样式为 `white-space: normal`，提示文字可见，截图目测无页面级横向溢出。
- 前端 26 项测试与生产构建通过；`git diff --check` 通过。命令行 Playwright 因 npm 离线缓存缺失未运行，改用应用内浏览器。未做多设备、多浏览器或打印布局验收。
- 附加 CSV 点击点测没有收到下载事件：API 日志仅见导出请求的 OPTIONS 预检，没有对应 POST；页面随后重载，故本轮**不声称**新文件名/新增 ID 列已由浏览器下载验证，也不能据此确定导出代码故障。上一轮静态/HTTP/单测证据仍有效，实际下载需在稳定浏览器环境重试。
- 隔离服务和临时数据库已停止并清理；未触碰主库或私有真实数据。实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
