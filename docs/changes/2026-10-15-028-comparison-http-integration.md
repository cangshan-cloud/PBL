# CHG-20261015-028：实验对比 HTTP 导出闭环回归

- 日期：2026-10-15
- 类型：HTTP integration regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

[前次改动](2026-10-15-026-comparison-group-dates-and-missing-ranks.md)为实验对比新增实际多空日期检查与 JSON/CSV/HTML 字段；已有测试只直接调用服务函数，尚未覆盖路由、序列化与下载响应。选择在既有隔离 `TestClient` 环境创建两条成功任务，再通过三个 HTTP 端点校验字段，避免借用或写入真实平台数据库。此轮仅增加验收防线，不改变服务计算逻辑。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 对比 JSON、CSV、HTML HTTP 闭环用例 | `backend/tests/test_api_journey.py::ApiJourneyTests.test_comparison_api_and_exports_include_actual_group_dates` | 防止接口字段或导出遗漏 |
| 接口验收说明 | `docs/EXPERIMENT_COMPARISON.md::导出` | 记录覆盖范围 |
| 总索引 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_api_journey.ApiJourneyTests.test_comparison_api_and_exports_include_actual_group_dates -v`：通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：172 项通过。
- `git diff --check`：通过。

## 风险、回退与未决事项

该测试运行在 Mac 的隔离 SQLite 内存数据库与临时数据目录，未验证浏览器下载交互或 OrbStack 队列；Ubuntu/Windows 由本提交对应的 CI 运行继续核对。任务使用合成演示数据，不形成市场有效性证据。
