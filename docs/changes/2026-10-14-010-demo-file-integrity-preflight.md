# CHG-20261014-010：演示预检增加数据文件完整性门槛

- 日期：2026-10-14
- 类型：tool + tests + documentation
- 状态：implemented
- 关联提交：与本记录同次提交

## 背景与目标

原演示预检仅检查数据目录记录。若 `demo_daily` CSV 或已发布历史包的本地文件在发布后丢失、被改动，目录仍会显示就绪，现场运行任务才失败。需要在不新建任务的前提下尽早发现。

## 决策过程

复用已有只读 `/datasets/{id}/preview` 路由：普通 CSV 会检查 SHA-256，历史包会检查清单和所有文件哈希。这样无需新增 API、数据库字段或另一套校验算法。普通模式总是校验 `demo_daily`；只有显式 `--require-historical` 才校验私有历史包，避免普通课程演示因未带私有包而失败。若目录存在多个已发布历史版本，逐一尝试，至少一个通过才视为可演示；每个失败原因会保留在最终错误中。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 预检调用数据预览、校验返回的版本和历史包元信息；历史请求超时设为 30 秒 | `tools/check_demo_readiness.py::ApiClient.request`、`check_readiness` | 目录存在但文件缺失/损坏时失败关闭 |
| 模拟正常、缺失 CSV、损坏历史包与只读调用 | `backend/tests/test_demo_readiness.py::FakeClient`、`DemoReadinessTests` | 防止预检退化为只看目录 |
| 更新彩排门槛和验证边界 | `docs/DEMO_REHEARSAL.md` 的“会前只读预检” | 团队可理解耗时与覆盖范围 |
| 登记变更 | `docs/CHANGE_INDEX.md` | 可追溯 |

## 验证与结果

- `python3 -m unittest tests.test_demo_readiness -v`：5 项通过，覆盖缺失和损坏时拒绝就绪。
- `make test`：116 项通过。
- 当前 `fbl` OrbStack 主栈的只读预检通过：前端、三账号、`demo_daily` 文件校验、六因子及查看者列表。主栈无已发布历史包，故不声称此环境的 `--require-historical` 成功。
- 项目既有历史包预览路由及整包校验已有单独自动测试；本轮未创建新任务，也未改动数据库内容。

## 风险、回退与未决事项

预检仅确认 API 容器能读取并验证文件，不证明 Worker 必定可读取同一挂载或任务可成功，亦不验证前端交互。历史包检查需读取所有文件，较目录查询耗时；30 秒超时若在低速磁盘上触发，应先检查环境，不应绕过校验。Windows 与团队多人环境仍未验收。
