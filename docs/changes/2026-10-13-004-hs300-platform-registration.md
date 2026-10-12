# CHG-20261013-004 历史沪深 300 包接入平台数据版本

- 日期：2026-10-13
- 状态：implementation / partial
- 决策依据：`DEC-20261012-009` 的不可变数据包、`DEC-20261012-011` 的既有演示隔离，以及 `CHG-20261013-003` 的离线封存结果。

## 修改内容与位置

- `backend/app/services/historical_bundle.py::verify_historical_bundle`：平台内校验清单摘要、固定研究口径、身份哈希、精确文件集合、符号链接及每个文件 SHA-256。
- `backend/app/services/datasets.py::register_hs300_bundle`：仅按固定包 ID 从 `DATA_ROOT` 同级的 `real/bundles` 注册草稿；`verify_dataset_file` 发布和存储审计时分流整包校验；`preview_dataset` 拒绝用单 CSV 预览误读历史包。
- `backend/app/main.py::register_historical_bundle`、`backend/app/schemas.py::HistoricalBundleRegistrationRequest`：管理员专用注册 API。
- `backend/app/services/runs.py::create_research_run`、`create_composite_run`：旧任务接口拒绝历史包，避免单 CSV 引擎误读清单。
- `backend/tests/test_historical_bundle_registration.py`：覆盖注册、发布、重复、篡改、多文件及路径穿越输入。
- `docs/HS300_BUNDLE.md`：写明注册调用、校验边界与尚不可运行的状态。

## 决策过程

现有 `DatasetVersion` 已有摘要、路径、状态和质量报告字段，故无需迁移；用 `quality_report.dataset_kind=hs300_bundle_v1` 区分，保持旧 CSV 路径不变。历史包只接受 ID 而非任意绝对路径，避免管理员接口成为文件系统探针。平台内实现独立的完整性校验以便 API/worker 容器使用，不依赖仓库根目录的离线工具。发布是第二次核验，以拦截注册后的文件改变。

## 验证

- `PYTHONPATH=backend .venv/bin/python -c '...verify_historical_bundle(...)...'`：真实私有包 576 个文件通过。
- `.venv/bin/python -m pytest -q backend/tests/test_historical_bundle_registration.py backend/tests/test_datasets.py`：14 通过。
- 全套后端测试结果另见本次提交前复验。

## 未决事项和限制

平台校验覆盖全文件完整性与清单身份，但未重复执行离线工具的逐行业务语义核验；若攻击者可同时改写整个包及清单，仍需离线复验或未来把语义校验移入平台。历史研究计算、报告与 t/t+1 审计尚未接通，因此不能对该包启动旧研究任务。私有数据包不进入 Git；另一台机器需要单独安全复制。当前仅验证 Mac 本地路径，Windows 部署仍延期。
