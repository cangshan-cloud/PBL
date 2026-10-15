# CHG-20261015-015：近期 Ubuntu/Windows CI 证据核对

- 日期：2026-10-15
- 类型：CI evidence + rehearsal gate
- 状态：verified for `11e0ce9`; later commits pending independent verification
- 关联提交：与本记录同次提交（文档提交本身的 CI 尚未核对）

## 背景与决策过程

验收矩阵只记录了较早的 `c376d4a` 跨平台成功结果，最近代码提交的 CI 状态尚未入档。课程答辩不能把旧提交的绿色作业当作当前版本证据。通过 GitHub 公开 Actions API 只读查询近期运行及最新作业；观察到 `54b86f6`、`0a7c453`、`fffad78`、`a1e64d1` 的运行均 `completed/success`，`11e0ce9` 的运行 #38742778282 中 Ubuntu 与 Windows `Verify` 作业均 `completed/success`。决定把精确提交与运行链接写入验收矩阵，并在彩排会前门槛加入“按演示提交核对 CI”的待勾选项，不把 CI 冒充 Windows 部署。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 更新近期跨平台 CI 证据和逐提交核对原则 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md::自动化与环境证据`、`下一步顺序与放行门槛` |
| 增加演示提交专属 CI 核对项 | `docs/FINAL_REHEARSAL_CHECKLIST.md::会前门槛` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- GitHub Actions [运行 #38742778282](https://github.com/cangshan-cloud/PBL/actions/runs/38742778282) 的公开 Jobs API：`Verify (ubuntu-latest)` 与 `Verify (windows-latest)` 均为 `completed/success`，head SHA 为 `11e0ce9`。
- 近期运行列表的公开 API：上述四个前序提交均为 `completed/success`。
- `git diff --check`：通过。

## 风险与未决事项

CI 只执行自动单测、黄金验算与前端构建；Mac OrbStack 实际服务、浏览器彩排、Windows/WSL2 部署和四人签收仍须分别完成。本次文档提交会触发新的 CI，不能自动继承 `11e0ce9` 的结果。
