# CHG-20261016-021：研究结果归属纳入前端自动回归

- 日期：2026-10-16
- 类型：前端可测试性与 CI 守护
- 状态：本机 Mac 测试通过；远端 Ubuntu/Windows CI 待核对
- 关联提交：与本记录同次提交；如提交受阻，以工作树状态为准

## 背景与决策过程

上一轮发现并修复“修改研究参数后旧结果仍显示”的产品误读问题，但仅有浏览器实测，没有持续自动回归。项目现有 CI 已在 Ubuntu/Windows 使用 Node 22 做前端构建，却没有前端测试步骤。决定不引入新的测试框架或浏览器依赖，而把纯参数与结果判断抽离为 TypeScript 模块，用 Node 22 内置测试运行器验证，并在构建前加入 CI。这样保留原有浏览器验收边界，同时让配置参数的后续改动更容易触发回归失败。

## 修改内容与代码位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 纯配置构造、可见性与标签函数 | `frontend/src/research-config.ts` | API 请求参数与结果键来自同一对象；历史／普通模式各按实际参数判定 |
| 工作台接入 | `frontend/src/main.tsx` 的 `buildResearchConfiguration`、`resultForConfiguration`、`longShortGroupLabel` 调用 | 保持上轮用户可见行为，减少重复逻辑 |
| 自动测试 | `frontend/tests/research-config.test.ts` | 七项跨平台纯函数回归 |
| 测试命令与 CI | `frontend/package.json`、`.github/workflows/ci.yml` | Ubuntu/Windows 构建前运行前端测试 |
| 验收、责任材料和索引 | `docs/FRONTEND_CONFIGURATION_REGRESSION_2026-10-16.md`、A/B/C/D 四责任包、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/CHANGE_INDEX.md` | 保留决策、执行者和验证边界 |

## 验证结果

Mac 本机 `npm test` 7 项、前端构建、后端 191 项与六观测黄金验算均通过。测试以纯函数验证，不创建新任务，也不把已验的上一轮浏览器行为表述为本轮重新浏览器实测。实际执行者：Codex。

## 风险与回退

Node 22 的 TypeScript 类型剥离在本机可运行，远端 CI 结果必须对本提交核对；若某平台执行环境不兼容，应修正测试入口而非删除结果归属测试。测试不能覆盖 React 事件、真实网络、Celery 或 Windows Docker 部署。回退本次纯函数和测试可恢复前一提交的内联逻辑，但会失去自动回归守护；不建议在课程验收前这样做。
