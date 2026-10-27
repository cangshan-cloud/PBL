# CHG-20261027-009 时间切分摘要与全区间序列核对

## 问题与决策

保存结果内部审计已经核对全区间计数、日期和多空成本，但带 `time_split` 的研究期/验证期摘要仍只由后端生成，没有离线交叉核对。决定以全区间逐日诊断和 IC/Rank IC 序列为只读参照，复算隔离日、两段观测/有效日期及摘要数值；这检查同源结果的内部一致性，不假装前瞻样本外或独立原始行情审计。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_research_result_consistency.py::verify_time_split_consistency`：有切分时复核最后一个切分前信号日隔离、两段起止/信号/观测/有效 IC 数和 IC/Rank IC 均值、ICIR、IC 为正比例；`verify_result_consistency` 先与任务参数中的预设切分日对齐再自动调用，旧无切分输出不变。
- `backend/tests/test_research_result_consistency.py::test_real_evaluator_split_and_embargo_tampering`：用正式研究计算器构造带切分结果并重签测试 JSON，证明隔离日、计数与摘要篡改被拒。
- `tools/verify_real_a_share_sample.py::validation_comparison_audit`：已有本机私有 10 股临时任务中，对动量/反转两条预设切分 Run 调用同一核对并输出摘要。
- `docs/SERIES_EXPORT_VERIFICATION.md`、`docs/TIME_SPLIT_VALIDATION.md`、[真实小样本只读验收](../REAL_SAMPLE_SPLIT_CONSISTENCY_QA_2026-10-27.md)、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：用法、真实执行结果和证据边界。

## 验证与未决事项

定向测试 6 项通过；原有私有 CSV SHA-256 未变，临时内存研究的动量/反转两条切分结果均核对通过：验证期各 58 个有效 IC 日；完整回归见本轮提交。未启动浏览器或主服务，真实浏览器切分 UI 仍只有此前构造响应的验收；不是本轮完成项。未重算 IC 数值、授权、可交易性或未来表现。
