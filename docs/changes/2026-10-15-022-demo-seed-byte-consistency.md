# CHG-20261015-022：内置演示数据种入使用同一字节快照

- 日期：2026-10-15
- 类型：seed data integrity + regression
- 状态：verified on Mac
- 关联提交：与本记录同次提交

## 背景与决策过程

检查内置 `demo_daily` 种入流程时确认：全新部署先读取样例 CSV 生成质量报告，再重新打开文件计算 SHA-256。若仓库样例文件恰好在两次读取间变化，就可能保存“旧内容质量报告＋新内容摘要”。与普通 CSV 预览和任务加载的已确认原则一致，决定只读取一次字节，同时用于 `validate_csv` 与 SHA-256；删除仅用于第二次读取的辅助函数。既有 `demo_daily` 版本不可变，不在启动时补写新质量字段。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 演示种入质量报告与摘要共用一次读取字节 | `backend/app/services/catalog.py::ensure_demo_catalog` |
| 模拟磁盘内容与读取快照不同，锁定报告及摘要同源 | `backend/tests/test_catalog.py::test_seed_quality_and_checksum_use_the_same_file_bytes` |
| 说明种入与旧版本行为 | `docs/DATASET_FORMAT.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- `.venv/bin/python -m unittest backend.tests.test_catalog -q`：1 项通过。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：162 项通过。
- `.venv/bin/python tools/verify_golden_research.py`：通过。
- `git diff --check`：通过。

## 风险与未决事项

这只确保单次种入所用字节一致，不是文件系统写保护；种入后若文件被外部修改，预览、研究任务和就绪预检的摘要复核仍会拒绝不一致。已有发布版本保持原质量报告；本轮未改前端、未复测浏览器或 Windows 部署。新提交的 CI 需单独核对。
