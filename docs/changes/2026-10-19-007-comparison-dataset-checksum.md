# CHG-20261019-007 实验对比披露数据版本 SHA-256

## 问题与决策

对比 JSON/CSV/HTML 已披露完整数据版本 ID，但该 ID 只定位数据库记录，跨环境核对相同数据字节还需版本校验和。决定直接读取 `DatasetVersion.checksum`，贯穿对比对象、CSV、HTML、页面口径表和离线校验器；不改变因子计算或历史任务产物。普通 CSV 版本的校验和对应导入文件字节，历史沪深 300 包版本对应 `manifest.json` 字节，不能混称为全部原始行情文件哈希。

## 修改位置

- `backend/app/services/comparisons.py`：每个对比任务新增 `dataset_checksum_sha256`，CSV 元数据列和 HTML 任务溯源表同步披露。
- `frontend/src/main.tsx`：对比类型与“实际研究口径”表显示完整校验和。
- `tools/verify_comparison_exports.py`：检查 JSON 校验和为 64 位小写十六进制，并核对可选 CSV/HTML 的同一字段。
- `tools/verify_real_a_share_sample.py`：核对真实样本对比结果、CSV、HTML 与采集清单的 SHA-256 一致。
- `backend/tests/test_comparisons.py`、`test_api_journey.py`、`test_comparison_export_verifier.py`：覆盖字段贯通及非法校验和拒绝。
- `docs/EXPERIMENT_COMPARISON.md`、`docs/REAL_A_SHARE_SAMPLE.md`、总索引和 A/B/C/D 四责任包：记录语义与验收边界。

## 验证与边界

定向后端 21 项、全量后端 214 项、前端 32 项测试通过，前端生产构建成功。私有 10 股固定快照只读复跑，采集清单 SHA-256 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652` 与对比结果及 CSV/HTML 一致；既有观测与验证期交集未变。本轮未重新做浏览器页面与下载点测，不能把测试说成浏览器验收。

哈希只辅助比对身份，不证明数据来源许可、文件可获得性、财务披露时点或研究结论有效。实际执行者：Codex。
