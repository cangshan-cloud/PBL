# CHG-20261014-020：黄金验算 CLI 窄编码兼容

- 日期：2026-10-14
- 类型：fix + test + docs
- 状态：implemented，远端 CI 待验证
- 关联提交：与本记录同次提交

## 背景与目标

提交 `2c5698f` 的公开 GitHub Actions [运行 #38540261543](https://github.com/cangshan-cloud/PBL/actions/runs/38540261543) 显示：Ubuntu 全部通过；Windows 后端测试已通过，但“Verify golden research results”失败。公开 API 只显示失败步骤，未给出断言文本。检查脚本发现全部验算结束后会向标准输出打印中文；本机运行 `PYTHONIOENCODING=cp1252 .venv/bin/python tools/verify_golden_research.py` 精确复现 `UnicodeEncodeError`，退出码 1。此处是本机复现支持的根因推断，最终以远端重跑为准。

## 决策过程

黄金验算脚本的成功提示不参与研究结果与课程文档，只是 CLI 状态。选择将终端提示改为 ASCII 英文，避免依赖 Windows 控制台代码页；保留中文研究说明文档。新增强制窄编码的子进程回归测试，比仅配置 CI 的全局 UTF-8 更能防止同类回归。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 成功提示改用 ASCII | `tools/verify_golden_research.py::main` | 窄编码终端不再因状态提示报错 |
| 子进程以 `cp1252` 标准输出运行黄金验算 | `backend/tests/test_golden_cli.py::GoldenCliTests.test_verifier_succeeds_with_windows_legacy_stdout_encoding` | 守护跨平台 CLI 输出 |
| 更新 CI 进展和本地证据 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md::自动化与环境证据` | 防止误称 Windows 已通过 |
| 登记变更 | `docs/CHANGE_INDEX.md` 对应条目 | 保留定位过程 |

## 验证与结果

- 修正前：`PYTHONIOENCODING=cp1252 .venv/bin/python tools/verify_golden_research.py` 在最终中文 `print` 抛出 `UnicodeEncodeError`。
- 修正后：相同命令通过；`.venv/bin/python -m unittest discover -s backend/tests -q` 共 130 项通过；`npm run build --prefix frontend` 通过；`git diff --check` 通过。
- 远端 CI：本记录编写时新提交尚未运行，不标记为通过。

## 风险、回退与未决事项

此修正不改变黄金样本计算或预期常数。若 Windows CI 仍失败，继续依据新的失败步骤定位；不能把本机复现当成远端通过。
