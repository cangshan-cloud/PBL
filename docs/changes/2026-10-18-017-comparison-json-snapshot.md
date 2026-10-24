# CHG-20261018-017 实验对比 JSON 快照下载

## 问题与决策

现有 CSV 混合任务明细与若干摘要区，适合人工查看但不能被当作单一矩形表稳定解析；HTML 更适合阅读。为了让研究人员程序化复核当前对比结果，增加页面端 JSON 快照下载。选择直接序列化已显示的对比对象，而非再请求一次服务端，以保证文件与页面此刻看到的结果一致；该文件不是新的持久报告，也不替代研究任务的复现材料。

## 修改位置

- `frontend/src/main.tsx`：对比摘要区新增“下载 JSON 快照”，以当前 `comparison.items` 顺序生成文件名，复用 Blob 下载组件；加载期间禁用。
- `frontend/src/comparison-download.ts`：文件名格式扩展到 `.json`，提供结构化 JSON 文本生成。
- `frontend/tests/comparison-download.test.ts`：验证基准顺序文件名和 JSON 解析回读。
- `docs/EXPERIMENT_COMPARISON.md`：解释三种格式的适用范围与复现边界。
- `docs/CHANGE_INDEX.md` 和 A/B/C/D 四份责任包：记录决策、验收与实际执行者。

## 验证与边界

前端 29 项测试通过，`npm run build` 成功。本轮没有重新做浏览器点击下载；浏览器行为仍以先前 CSV/HTML 实测为历史证据，JSON 的实际浏览器落盘需另行复点。JSON 快照不含原始逐股行情和逐股观测产物，不能独立重算研究结果。实际执行者：Codex。
