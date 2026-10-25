# CHG-20261025-005 历史 API 验收导出关联校验

## 问题与决策

原隔离 API 验收脚本在四份文件内部一致后返回成功，但未比对下载的复现包是否属于刚创建的历史任务及指定私有包。决定增加任务 ID、成功状态、数据集 ID、封存包 ID 和五分组参数的明确关联检查；异常或缺失结构直接失败。实际执行者：Codex。

## 修改内容与对应位置

- `tools/verify_historical_api_journey.py::verify_journey_binding`、`run_journey`：四文件一致性通过后，读取已验证复现包并确认其关联身份。
- `backend/tests/test_historical_api_journey.py`：正例、交叉任务/数据集/包/分组及畸形结构反例。
- `docs/ORBSTACK_DEPLOYMENT.md`、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：记录验收口径。

## 验证结果与未决事项

定向 5 项通过；本机既存私有当前导出与其任务、数据集和包 ID 绑定检查通过。全量回归和文档核对见本轮提交。OrbStack Docker socket 仍不可用，没有重跑隔离 Celery/HTTP 链路；未触碰主栈或数据卷。该关联校验不验证行情来源授权、独立因子公式或真实可成交收益，也不代替队长本人产品实测；用户修改的分工 Excel 未处理。
