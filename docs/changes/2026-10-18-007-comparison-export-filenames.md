# CHG-20261018-007：实验对比导出文件名标记任务组合

## 背景与决策

上一轮真实浏览器下载确认功能可用，但任意组合均保存为 `factorlab-comparison.csv` 或 `.html`。研究员连续比较不同任务时，下载目录中的文件难以从名称辨认来源；浏览器自行附加的重名序号也不表达基准任务。决定在浏览器文件名中按选择顺序加入每个 Run ID 的前 8 位，首位对应基准。保持 API 路径、请求、文件内容及数据库记录不变。短 ID 仅用于人工辨认，不能替代文件内部的完整 Run ID；极端前缀碰撞仍应以文件内容为准。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 文件名构造与基准顺序 | `frontend/src/comparison-download.ts::comparisonDownloadFilename` |
| 浏览器导出时使用当前请求的 Run ID 快照 | `frontend/src/main.tsx::downloadComparison` |
| 文件名顺序、不同组合回归 | `frontend/tests/comparison-download.test.ts`、`frontend/package.json` |
| 口径文档、总索引及四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 前端 25 项测试通过，生产构建通过；`git diff --check` 通过。
- 示例：基准 `aaaaaaaa-…` 与候选 `bbbbbbbb-…` 导出为 `factorlab-comparison-aaaaaaaa-bbbbbbbb.csv`；反转顺序则文件名反转。不同组合不再共享固定默认名。
- 本轮未重跑后端测试、真实行情脚本或浏览器下载点击；上一轮的实际下载验收仍仅覆盖改名前版本。本轮也未解决 HTML 打印视觉排版限制。
- 实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
