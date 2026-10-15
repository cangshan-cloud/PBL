# CHG-20261015-002：历史研究任务重试保持原模式

- 日期：2026-10-15
- 类型：bug fix + API regression
- 状态：本机测试通过
- 关联提交：与本记录同次提交

## 背景与决策过程

通用重试接口此前只识别 `composite`；其余任务一律交给普通单因子创建器。失败或取消的 `historical_hs300_2024` 任务因此会在重试时被当作普通任务，而历史数据包明确只能由专用模式使用，导致重试失败。选择根据原实验保存的 `mode` 分流到已有的三个创建器，保留各模式自己的数据与参数约束，不增设第四套任务逻辑。若数据版本已不可用，返回明确的 400/404；不把失败伪装为排队成功。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 历史模式进入 `create_historical_run`；创建校验错误映射到 HTTP 状态 | `backend/app/main.py::retry_task` |
| 隔离 API 覆盖研究员重试、查看者拒绝、原任务不变、模式/分组保持、数据撤销发布时失败 | `backend/tests/test_api_journey.py::ApiJourneyTests.test_failed_historical_task_retries_in_historical_mode` |
| 明确三类任务的重试语义 | `docs/TASK_EXECUTION.md::接口与权限` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_api_journey.ApiJourneyTests.test_failed_historical_task_retries_in_historical_mode -q`：通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：140 项通过。
- 使用 SQLite 内存库与 mock 队列，只验证 API 创建、权限、参数及排队调用；未向现有 OrbStack 栈创建任务。

## 风险与未决事项

历史私有包在任务执行阶段仍须通过文件与哈希检查；API 重试通过不等于真实行情计算通过。本次不改变成功任务不可重试的规则，也不对现有失败任务自动重新排队。Windows Compose 环境仍未实测。
