# CHG-20261019-011 实验对比披露数据来源性质

## 问题与决策

对比结果已显示数据版本、完整 ID 和 SHA-256，但这些身份信息不说明数据是内置演示快照、历史研究包还是用户导入 CSV。课程验收中，演示数据的高收益或 IC 容易被误读为真实市场结论。决定在每条对比任务中增加来源类别，并贯通页面、JSON 快照、CSV 与 HTML；“导入”只描述进入平台的方式，绝不自动认证其真实性、许可或财务披露时点。

分类依据为平台已保存的内部元数据：仅 `demo_daily` 且标有 `bundled_demo` 的版本识别为 `bundled_demo`；仅 `hs300_2024` 且为历史包类型的版本识别为 `historical_bundle`；其余均为 `imported_csv`。这样普通用户上传的任意 `source` 文本不能伪装成内置演示源。

## 修改位置

- `backend/app/services/comparisons.py`：对比项新增 `dataset_source_kind`；CSV 增加同名列，HTML 的数据版本号单元格附来源中文标签。不改变研究指标、排序或可比性警告。
- `frontend/src/comparison-format.ts`、`frontend/src/main.tsx`：对比页新增“数据来源性质”说明，内置演示数据明确写明“结果仅用于功能验收”；未知类别显示“未记录”，不误归类为导入数据。
- `tools/verify_comparison_exports.py`：校验新字段及 CSV/HTML 一致性，仍兼容没有该可选字段的旧版 JSON/CSV/HTML 下载文件。
- `backend/tests/test_comparisons.py`、`backend/tests/test_comparison_export_verifier.py`、`frontend/tests/comparison-format.test.ts`：覆盖三种分类、用户元数据伪装、格式贯通和错配拒绝。
- `docs/EXPERIMENT_COMPARISON.md`、总索引和 A/B/C/D 四责任包：记录口径与验收证据。实际执行者：Codex。

## 验证

后端定向 21 项、全量 215 项通过；前端 33 项测试和生产构建通过。隔离 Mac 浏览器运行演示动量与反转后，对比页两任务均显示“内置演示数据；结果仅用于功能验收”。新三格式实际浏览器下载文件位于 Downloads，离线联验返回 2 任务、2 警告，CSV/HTML 均通过。旧三格式浏览器文件在兼容路径下也通过。首次 HTML 下载时页面返回总览且未收到下载事件；恢复同一组合后重试成功，未放宽校验。

## 边界

这是数据入口类别标识，不是原始数据审计或第三方来源证明；`historical_bundle` 也不能仅凭类别推断包内行情许可。浏览器实测仅覆盖演示数据和 Mac，未重新验收真实样本浏览器流程或 Windows。三份新下载文件保留供本机复核，隔离服务与临时数据目录已清理。
