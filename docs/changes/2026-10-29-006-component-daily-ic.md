# CHG-20261029-006 成分 IC 逐日序列留存与导出

## 问题与决策

原结构化结果只保存成分 IC 均值和有效日期数，逐日计算值被丢弃，研究员无法查看时间稳定性或独立复算摘要。决定仅对新 Run 保存共同样本上的逐日 IC、Rank IC 与样本数，保留无法计算日的 `null`；摘要仍按有效日期算术平均。任务中心对完整逐日字段提供 CSV，旧版仅有摘要的 Run 不显示该按钮。独立结果审计核对日期、样本数、有效日与均值，不改变组合、分组或交易收益。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 每成分逐日记录 | `backend/app/domain/composite.py::combine_factor_observations` | 留存均值依据及不可计算日 |
| 逐日结果一致性审计 | `tools/verify_research_result_consistency.py::_verify_component_ic_daily` | 检测摘要、日期和样本数被篡改或不一致 |
| 新导出格式、旧 Run 条件入口 | `frontend/src/component-ic-export.ts::componentIcDailyCsv`、`ComponentIcTable.tsx::ComponentIcRow`、`main.tsx` 任务详情区 | 完整 Run ID 绑定的原值 CSV |
| 构造样本、反例及导出测试 | `backend/tests/test_composite.py`、`backend/tests/test_research_result_consistency.py`、`frontend/tests/component-ic-export.test.ts` | 固定空值、均值和向后兼容边界 |
| 研究口径、真实验收、索引及四责任包 | `docs/MULTI_FACTOR_ANALYSIS.md`、`docs/HISTORICAL_COMPONENT_IC_DAILY_QA_2026-10-29.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 保留决策、结果和团队材料 |

## 验证与未决事项

后端 329 项、前端 89 项、生产构建和 Golden Research 检查通过。只读私有包内存 Run 四成分各 242 日；移除新增 `daily` 后整个结果与前轮逐字段相等，严格 V2 和一致性审计通过。隔离 Celery 新 Run `2e898f44-7d5a-4e82-912b-6ddfab4b512f` 的实际浏览器 CSV 有 968 行，四因子各 242 日及 72,366 样本数；HTTP V2 三项校验通过。旧摘要 Run 无逐日按钮，隔离项目关闭后主 `fbl` 仍 `running(5)`。队长人工验收、Windows 和数据来源授权核验未进行；用户修改的 Excel 不处理。台账、链接与差异检查随提交执行。
