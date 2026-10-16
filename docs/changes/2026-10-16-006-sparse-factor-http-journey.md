# CHG-20261016-006：稀疏因子日期 HTTP 闭环验收

- 日期：2026-10-16
- 类型：HTTP integration regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

此前已分别用单元测试覆盖全截面因子同值、每日样本数不足、报告与结论提示，但缺少一个从 CSV 上传到任务、复现包、结论、报告的完整流程。决定在隔离内存数据库和临时文件目录中生成小型 `pe` 因子 CSV，构造一日全同值、两日可用证券不足和一日正常分组；再限制日期范围形成“没有任何可分组日”的任务。此测试只验证软件对稀疏样本的诚实表达，不宣称因子有效性或真实市场表现。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 上传、发布、研究、复现、结论、报告闭环及全跳过分支 | `backend/tests/test_api_journey.py::ApiJourneyTests.test_sparse_factor_dates_are_disclosed_across_task_conclusion_and_report` | 防止跨层披露口径不一致 |
| 验收说明 | `docs/SINGLE_FACTOR_ANALYSIS.md::结果输出` | 标明空多空结果不补零 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_api_journey.ApiJourneyTests.test_sparse_factor_dates_are_disclosed_across_task_conclusion_and_report -v`：通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：178 项通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

样例日期是合成的连续日期，只验证接口与研究口径，不代表交易所日历。测试在 Mac 的隔离 SQLite/临时目录执行，未覆盖 OrbStack Worker 或 Windows 浏览器；最终彩排仍需由团队成员实际操作并署名。无应用运行时代码改动。
