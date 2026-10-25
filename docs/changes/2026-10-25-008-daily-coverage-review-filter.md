# CHG-20261025-008 逐日待核对日期筛选

## 问题与决策

真实历史任务 242 个交易日里有 107 日存在未形成观测，但 IC 与分组状态仍可计算；全年分页后仍需逐页查找。决定增加显示层“只看待核对日”，定义为未形成观测大于零或 IC／分组不可计算。名称与说明不推断原因，因为回看预热、末尾无标签等亦可能导致差额。筛选不改全量结果及导出。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/daily-coverage.ts::needsCoverageReview`、`selectCoverageRows`：明确筛选谓词并保持原顺序。
- `frontend/src/DailyCoverageTable.tsx::DailyCoverageTable`：复选框、解释文案、筛选计数、重置页码及空结果。
- `frontend/src/styles.css`：筛选行样式。
- `frontend/tests/daily-coverage.test.ts`：间隙/不可计算状态、顺序与分页边界测试。
- `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/HISTORICAL_COVERAGE_FILTER_QA_2026-10-25.md`、索引及 A/B/C/D 责任包：记录语义和真实浏览器验收。

## 验证结果与边界

前端 54 项测试及生产构建通过。专用 OrbStack 容器中的研究员浏览器任务成功；筛选 107/242 日、6 页，第二页首日与恢复全量首页均实点通过，控制台错误/警告 0。全量回归与文档检查见本轮提交。未将差额判定为停牌或数据质量错误；未做独立行情核验、Windows 或队长本人产品实测。用户修改的分工 Excel 保持原样。
