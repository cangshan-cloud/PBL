# CHG-20261015-016：CSV 校验与解析使用同一字节快照

- 日期：2026-10-15
- 类型：data integrity + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

正式研究任务原先先 `read_bytes()` 计算 SHA-256，随后重新 `open()` 解析 CSV；数据预览原先先校验文件，再重新打开读取前几行。若文件在两次读取间发生外部变更，校验与实际计算或展示可能针对不同内容。决定在两个入口各读取一次文件，并对读到的同一份字节同时计算 SHA-256 与解析 CSV，不改变数据库版本、API 字段或既有校验错误。CSV 默认上传上限 25MB，内存快照是当前课程范围可接受的取舍；若以后扩大文件上限，需要重新评估流式解析与锁定策略。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 研究数据文件单次读取、校验与解析 | `backend/app/services/sample_data.py::load_price_file` |
| 数据预览读取已校验的同一字节快照；发布仍调用完整性检查 | `backend/app/services/datasets.py::_read_verified_csv`、`preview_dataset`、`verify_dataset_file` |
| 文件磁盘内容与模拟已校验快照不同的回归案例 | `backend/tests/test_sample_data.py`、`backend/tests/test_datasets.py::test_preview_parses_the_verified_byte_snapshot` |
| 补充格式说明和验收证据 | `docs/DATASET_FORMAT.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_sample_data backend.tests.test_datasets -q`：16 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：155 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险与未决事项

这保证**单次读取获得的字节**同时用于校验与解析，不等于文件系统快照或持久锁；文件在读取期间被恶意并发改写仍需操作系统级防护。CSV 预览和研究执行会暂存整份原始字节，超出默认 25MB 上限时需审视内存。历史沪深 300 私有包有独立的多文件验证路径，不在本次修正范围；旧报告不会重算。本次提交的 CI 需要另行核对。
