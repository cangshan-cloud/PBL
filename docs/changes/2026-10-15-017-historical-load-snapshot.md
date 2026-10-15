# CHG-20261015-017：历史包实际加载文件再核验字节

- 日期：2026-10-15
- 类型：historical data integrity + regression + private-bundle smoke
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

历史任务原先先核验 576 个封存文件及清单，随后分别重新打开日历、成员和行情 CSV 解析；若文件在核验与加载之间改变，计算可能使用未经核验的字节。决定保留整包预检以核对文件集合与所有摘要，再对每个真正参与解析的 CSV 按清单摘要复验其单次读取到的字节，从该字节快照解析。逐文件处理避免同时持有整包原始内容；不修改封存格式、因子公式或私有源数据。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 单文件读取、清单摘要复验并从同一字节解析 | `backend/app/domain/historical_research.py::_verified_csv_rows` |
| 日历、成员、逐证券行情全部使用复验读取 | `backend/app/domain/historical_research.py::load_historical_bundle` |
| 模拟磁盘内容与已校验快照不同及篡改拒绝 | `backend/tests/test_historical_research.py::test_historical_csv_parser_uses_only_verified_bytes` |
| 边界、真实包加载证据和验收矩阵 | `docs/HS300_BUNDLE.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_historical_research -q`：6 项通过。
- 本机 Git 忽略的封存包 `hs300_2024_0375298bd2c8ac52` 只读调用 `load_historical_bundle` 并核对已记录清单摘要：292 个交易日、242 个成员日、328 只证券、95,776 条行情，均与既有记录一致；未创建任务或改数据库。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：156 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险与未决事项

逐文件校验不是文件系统锁或原子目录快照；并发恶意修改同一文件的读取过程仍不在本方案保证之内。最初全包核验之后新增但未参与加载的文件不会被第二次扫描，受控私域部署和权限管理仍重要。真实包不随 Git 分发，其他机器需要独立取得并核验。Windows、浏览器和队列端到端未在本轮复测；新提交的 CI 需独立核对。
