# CHG-20261015-020：CSV 质量报告提示证券活跃期内部断档

- 日期：2026-10-15
- 类型：data quality + UI indication + regression
- 状态：verified by Mac tests and build; browser not rerun
- 关联提交：与本记录同次提交

## 背景与决策过程

CHG-20261015-019 已让普通 CSV 因子跳过证券缺失市场日，但研究人员难从原质量报告看出是否存在这类输入。决定增加**信息性**断档计数：以 CSV 全部证券的日期并集推断日历，统计每只证券从首条到末条记录之间缺少的日期数，并统计受影响证券数。它不把上市前/退市后空白算作断档，不拒绝上传、不自动补值，也不将断档解释为停牌或错误；全体同日缺行仍不可见。前端在数据集卡片显示总数，非零时解释范围；旧已保存质量报告无新字段时显示“—”。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 导入质量报告增加推断市场日数、活跃期断档数、受影响证券数 | `backend/app/services/datasets.py::validate_csv` |
| 覆盖个别证券内部缺行与晚起始证券不计入 | `backend/tests/test_datasets.py::test_reports_internal_symbol_gaps_without_rejecting_csv` |
| 数据集卡片显示断档数和非零提示，旧版本显示未知 | `frontend/src/main.tsx::QualityReport`、数据集视图 |
| 解释字段定义、局限和验收状态 | `docs/DATASET_FORMAT.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_datasets -q`：15 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：159 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `npm run build --prefix frontend`：通过。
- 本机 Git 忽略的 BaoStock 10 股 CSV 只读运行 `validate_csv`：117 个推断市场日、0 个活跃期内部断档、0 只受影响证券；未导入新平台版本。
- `git diff --check`：通过。

## 风险与未决事项

断档基于**整份 CSV**，而普通研究任务可只选部分证券；选择子集后推断日历和任务跳过情况可能不同。全体证券同日缺行及数据源实际停牌原因无法由该统计证明。旧数据集质量报告保持不可变，UI 的“—”是未知，不是零。本轮未做真实浏览器点击验收；新提交 CI 与 Windows 部署需独立核对。
