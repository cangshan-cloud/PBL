# CHG-20261015-014：多因子合成拒绝非法权重

- 日期：2026-10-15
- 类型：research input integrity + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

先核对代码指纹：现有 `backend/app/versioning.py::source_fingerprint` 已覆盖 `backend/app/` 全部 Python 源文件和 `backend/pyproject.toml`，近期研究引擎变更会改变指纹，无须修改。随后检查多因子合成：课程产品只创建等权参数，但底层合成函数允许 `NaN`、无穷或权重求和溢出。`NaN` 比较可能绕过原有非负/正和检查，极大有限权重的总和也可能变为无穷并造成无意义的归一化。决定在归一化前明确拒绝非有限、负数、零总和和非有限总和，不新增用户自定义权重功能。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 有限非负权重及有限正总和校验 | `backend/app/domain/composite.py::combine_factor_observations` |
| `NaN`、正负无穷及有限权重求和溢出回归 | `backend/tests/test_composite.py::test_rejects_invalid_components_and_weights` |
| 说明底层边界与等权产品范围 | `docs/MULTI_FACTOR_ANALYSIS.md` |
| 同步验收矩阵证据 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_composite -q`：6 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：152 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险与未决事项

现有等权任务行为不变；只有非法底层调用会从后续计算异常或错误数值改为明确报错。该检查不提供任意权重输入，也不证明多因子经济有效性。新提交的 CI 结果需独立核对，不能沿用旧提交的成功记录。
