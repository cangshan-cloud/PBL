# CHG-20261018-001：旧任务缺观测产物时的可比性降级

## 背景与决策

实验对比允许读取早期没有逐股观测产物的 Run。此前严格样本区会说明不可用，但若其他口径检查无警告，顶部 `comparable` 仍可能为 `true`，CSV 显示“通过”、页面使用绿色状态。这容易把仅按日期对齐的比较误读为已核对同股票样本。

决定在任何所选 Run 缺少逐股观测产物时，增加明确警告并把总体可比性降为“谨慎解释”。不拒绝请求、不补造旧产物、不改写已保存的 Run；原全区间指标、共同日期和已保存验证期摘要继续可看。正常无警告时，页面与 HTML 也仅称“所列口径检查通过，仍属描述性回溯”，不暗示未来有效性。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 缺产物警告及 `comparable` 降级 | `backend/app/services/comparisons.py::compare_runs` |
| HTML 成功状态措辞 | `backend/app/services/comparisons.py::comparison_html` |
| 页面成功状态措辞 | `frontend/src/main.tsx` 实验对比摘要 |
| 旧产物缺失时 API、CSV、HTML 与仍可查看日期摘要的回归；另在原本无警告的组合中单独验证降级 | `backend/tests/test_comparisons.py::test_validation_split_comparison_discloses_mixed_and_different_cutoffs`、`test_matching_effective_dates_are_comparable_despite_different_lookbacks` |
| 口径、索引与四人责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- Mac 本机后端 209 项测试、前端 16 项测试与生产构建通过。
- 缺产物仅表示无法做严格同样本核对，并不意味着旧任务的原指标必然错误；仍可进行有限的共同日期诊断。
- 本轮未做浏览器、Compose/Celery、Windows 或真实行情的新验证。测试由 Codex 代执行，不代表四名成员本人签收。
