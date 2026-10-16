# CHG-20261016-014：Compose 写入式验收入口显式确认

- 日期：2026-10-16
- 类型：验收工具安全与回归
- 状态：Mac 本机验证通过；未执行新的 Compose 写入任务
- 关联提交：与本记录同次提交

## 背景与决策过程

`verify_compose_stack.py` 与 `verify_compose_real_sample.py` 原先默认连接本机 8000 端口。只要环境中已有密码，误运行便可能向主 `fbl` 栈写入研究任务；真实样本脚本还可能上传／发布数据集。历史任务脚本已有显式写入确认。决定给这两个入口统一增加两个条件：操作者显式设置 `FACTORLAB_SMOKE_URL`，并传 `--acknowledge-writes`。两条件必须在读取私有样本或网络请求之前检查。选择通用 flag 是因为也可能在明确允许留记录的主栈验收；不把“只允许隔离栈”伪装成程序能验证的规则。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 共用前置门槛 | `tools/verify_compose_stack.py::require_explicit_write_target`、`main` | 缺条件即以退出码 2 停止，无请求 |
| 真实样本入口复用门槛 | `tools/verify_compose_real_sample.py::main` | 上传／发布和六项任务前先检查 |
| 防误操作测试 | `backend/tests/test_compose_stack_verify.py::ComposeStackSnapshotTests` | 缺确认、缺 URL、不读取样本及确认后可继续登录 |
| 操作说明 | `docs/ORBSTACK_DEPLOYMENT.md`、`docs/REAL_A_SHARE_SAMPLE.md` | 命令加入 URL 与 flag，说明仍须人工核对目标 |
| 四人责任包 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` | 本轮每包写明实际执行者、证据和边界 |
| 总索引 | `docs/CHANGE_INDEX.md` | 按变更号追溯 |

## 验证与结果

后端 189 项测试、固定黄金样例、私有 10 股真实样本五因子回归、前端生产构建、`git diff --check` 通过。新增测试使用 mock 断言缺确认时没有请求或私有文件读取、缺显式 URL 时没有请求；确认和 URL 均有时可进入登录步骤。未启动新 Compose 任务，不把单测门槛当成新的 Worker 验收。实际执行者：Codex。

## 风险、回退与未决事项

显式 flag 和 URL 只能降低误操作，不能识别填入的是主栈还是隔离栈；真实验收前仍须人工核对端口、Compose 项目、数据库卷和运行目录。默认 URL 常量仍用于只读请求函数兼容，但主入口不会在缺显式环境变量时执行。Windows、多人负载、正式十分钟口头演示仍未覆盖。若回退本变更，两个脚本恢复原有误写风险，应同步恢复文档命令与测试。
