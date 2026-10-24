# CHG-20261022-001 变更台账校验纳入 CI

## 问题与决策

上一轮新增的台账反例测试使用 pytest 函数与 `tmp_path`，本机 pytest 可运行，但项目 CI 使用 `python -m unittest discover`，因此这四项不会被发现。决定保持现有 CI 测试框架，将测试改成 `unittest.TestCase` 和标准库临时目录，并在现有 Ubuntu/Windows 作业中显式运行只读台账命令；不增加第三方测试依赖，也不改研究服务。实际执行者：Codex。

## 修改内容与位置

- `backend/tests/test_change_ledger.py::ChangeLedgerTests`：四个原有正反例改成 unittest 可发现用例，仍使用隔离临时仓库夹具。
- `.github/workflows/ci.yml` 的 `Verify change ledger` 步骤：后端测试后执行 `python tools/check_change_ledger.py`，适用于当前双系统矩阵。
- `docs/CHANGE_INDEX.md`：补充 CI 契约与本记录；`docs/DEVELOPMENT_PLAN_2026-10-21.md` 与 `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` 更新本机后端测试计数；A/B/C/D 责任包记录本轮各自验收边界。

## 验证与边界

本机执行与 CI 相同的 unittest discovery：**253 tests OK**（含 4 个台账用例）；定向四用例亦通过；`tools/check_change_ledger.py` 返回 PASS：173 条已索引记录、11 条近期 CHG 均链接四责任包；`git diff --check` 通过。工作流改动尚须推送后由 GitHub Actions 运行才能声称 Ubuntu/Windows CI 成功；本机测试不能替代远端结果。本轮不启动容器、不重做浏览器或真实数据验收。
