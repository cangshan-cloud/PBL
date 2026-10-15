# CHG-20261015-021：普通研究任务先取全数据集日历再筛选证券

- 日期：2026-10-15
- 类型：research time alignment + API regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

CHG-20261015-019 修正了个别证券缺行跨日取标签的问题，但其日历从传入因子函数的行推断。正式任务先筛选证券，若只选的证券全体同日缺行，而未选证券在该日有记录，该市场日会从筛选后日期并集中消失。数据集本身已有可用证据，因此决定任务在筛选前构建整份已发布 CSV 的日期位置表，并传给单因子与多因子全部内置因子；仅研究对象仍按用户选择。底层直接调用 `calculate_factor` 不提供位置表时保持从传入行推断，方便独立计算和既有工具。仍不把日期并集冒充独立交易所日历。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 内置因子共用可注入的市场日期位置表 | `backend/app/domain/factors.py::FactorDefinition`、`calculate_factor`、各内置计算器 |
| 任务加载全数据集后、筛选证券前计算位置表，传入单/多因子 | `backend/app/services/runs.py::execute_research_run` |
| 底层只选 A 时全量日期揭示缺口 | `backend/tests/test_factors.py::test_full_dataset_calendar_detects_gaps_after_symbol_selection` |
| 真实 API 上传、发布、仅选 A/B，未选 C 提供日历的回归 | `backend/tests/test_api_journey.py::test_selected_symbols_keep_full_dataset_market_calendar` |
| 当前口径、证据与索引 | `docs/SINGLE_FACTOR_ANALYSIS.md`、`docs/SAMPLE_SELECTION.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_factors backend.tests.test_api_journey.ApiJourneyTests.test_selected_symbols_keep_full_dataset_market_calendar -q`：8 项通过；API 案例返回成功，覆盖量 8（旧筛选后日历会为 10）。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：161 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- 本机 Git 忽略的同一 SHA-256 真实 10 股 CSV 只读计算，选择 `600000.SH`、`600276.SH`：动量 192 个观察/96 日期，PE 232 个观察/116 日期；未创建平台任务。
- `git diff --check`：通过。

## 风险与未决事项

新任务在有缺口且选择子集时，可能比旧任务少观测；旧任务与报告不重写。日期并集仍无法发现数据集所有证券同日缺行，也不提供停牌、涨跌停或独立交易所日历。质量报告的内部断档数按整份 CSV 统计，与任务中的所选子集覆盖量不是同一个指标。新提交的 CI、真实容器队列与 Windows 部署需单独核对。
