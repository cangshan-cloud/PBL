# CHG-20261018-011：实验对比页面显示数据版本身份

## 背景与决策

对比后端已经按完整 `dataset_version_id` 判断是否为同一数据版本，上一轮也在 CSV/HTML 导出中披露了该 ID；但页面候选列表与“实际研究口径”表只显示版本号。两个独立数据版本可能都叫 `0.2.0`，研究人员在页面看到“数据版本不同”警告时无法就地核对。决定在候选列表显示短 ID，兼顾扫描；在已生成对比的口径表显示完整 ID，提供准确追溯。缺少旧任务 ID 时列表仅显示版本号，不伪造身份。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 候选列表显示版本号与短 ID，详细口径表显示完整 ID | `frontend/src/main.tsx` 实验对比视图、`ComparisonItem` 类型 |
| 长 ID 单元格允许换行 | `frontend/src/layout.css::.comparison-dataset-id` |
| 候选标签生成与同名版本区分测试 | `frontend/src/comparison-format.ts::comparisonDatasetLabel`、`frontend/tests/comparison-format.test.ts` |
| 口径文档、总索引与四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- 前端 26 项测试通过，生产构建通过；`git diff --check` 通过。
- 本轮未改后端 API、比较警告、计算或导出文件；也未重跑后端/真实样本验证。短 ID 只是选择辅助，精确核对应看详细表中的完整 ID。
- 未做浏览器截图、窄屏横向滚动或打印视觉验收。实际执行者：Codex；四人责任包为代执行记录，非成员本人签收。
