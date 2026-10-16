# CHG-20261016-022：研究参数提交前校验

- 日期：2026-10-16
- 类型：产品输入边界与前端回归
- 状态：Mac 本机测试通过；远端 CI 与浏览器交互未核对
- 关联提交：与本记录同次提交

## 背景与决策过程

工作台的数字输入允许暂时清空；React 将空值转换为 `NaN`，现有“运行研究”按钮仍可发送请求。日期也可能因手工修改而倒置或越过数据版本范围，导致后端报错而非在配置区解释。课程演示应避免无效任务打断，因此在 API 提交前增加轻量纯函数校验。后端 Pydantic 校验仍是最终边界；此处不更改研究算法、数据版本或服务接口，也不自动篡改用户输入。

## 修改内容与代码位置

| 内容 | 位置 |
| --- | --- |
| 检查 2～10 整数分组、单因子 2～120 整数回看窗口、0～100 有限成本、多因子 2～6 个成分、样本日期顺序与数据版本范围；历史模式只校验其实际可配的分组 | `frontend/src/research-config.ts::validateResearchConfiguration` |
| 配置区直接显示错误，点击运行时在请求发出前阻止无效参数 | `frontend/src/main.tsx` 的 `researchInput`、`researchValidationError` 与 `runResearch` |
| 增加两个测试用例覆盖 `NaN`、越界、隐藏参数和日期错误 | `frontend/tests/research-config.test.ts` |
| 本记录、验收矩阵和四责任包 | `docs/changes/2026-10-16-022-research-input-preflight.md`、`docs/CHANGE_INDEX.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/member-deliverables/` |

## 验证与边界

实际执行者：Codex。Mac 上前端 9 项、生产构建、后端 191 项和固定六观测黄金验算通过；`git diff --check` 通过。本轮为纯函数和构建验证，未重新运行浏览器、Celery、Compose 或 Windows 部署；远端 CI 需逐提交核对。浏览器 `type=number` 的原生控件行为会随浏览器而异，后续正式彩排仍应试一次非法输入提示。

## 风险与回退

前端校验仅面向当前 UI 参数，不替代后端校验；未来新增参数必须同步更新校验测试。若日期来源口径改变，需重新审查“不得越过数据版本起止日”规则。回退本次前端校验不会改变后端拒绝逻辑，但会退回不友好的提交后报错。
