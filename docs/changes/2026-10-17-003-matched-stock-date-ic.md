# CHG-20261017-003：共同证券日期的严格样本 IC 对比

- 日期：2026-10-17
- 类型：研究可比性与产物完整性
- 执行者：Codex
- 状态：Mac 本机自动回归通过；未做浏览器手工或 Compose 联调

## 决策过程

上一轮共同日期 IC 摘要仅对齐日期，无法判断同一天是否由相同证券构成截面。考虑到少量研究人员、课程项目和后续真实数据，决定为**新任务**保存原始有效观测（因子值、次日收益、证券、日期）的独立 gzip 文件，SHA-256 绑定产物记录；不把逐股明细塞入常规指标 JSON 或任务列表。对比时取所有 Run 的共同证券日期键，按每个 Run 原预处理配置重算 IC 类指标。旧任务无此产物时保持原有对比并明确降级，不尝试从报告反推逐股数据。收益标签不同要警告；此功能不重算多空、换手或交易成本，避免夸大为同口径交易回测。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 观测文件压缩、校验和、读取与计数验证 | `backend/app/services/observation_artifact.py` |
| 普通、组合及历史 Run 成功产物中加入观测文件 | `backend/app/services/runs.py::execute_research_run` |
| 共同证券日期交集与原预处理口径 IC 重算、收益标签差异提示；旧 Run 降级 | `backend/app/services/comparisons.py::compare_runs` |
| JSON、CSV、HTML 与页面分别显示严格样本摘要 | `backend/app/services/comparisons.py::comparison_csv`、`comparison_html`、`frontend/src/main.tsx` 实验对比区 |
| 测试 | `backend/tests/test_observation_artifact.py`、`backend/tests/test_comparisons.py`、`backend/tests/test_persistence.py` |
| 文档与四责任包 | `docs/EXPERIMENT_COMPARISON.md`、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` |

## 验证与边界

- `.venv/bin/python -m unittest discover -s backend/tests`：196 项通过，包括隔离 HTTP JSON／CSV／HTML 对比闭环及收益标签差异提示。
- `npm run build`、`npm test -- --run`：构建与 13 项测试通过。
- 校验和篡改与文件缺失会拒绝读取；旧任务缺少新产物仍返回原始和共同日期摘要。
- 未重采真实市场数据，未做完整同口径回测或统计显著性论证；本轮未启动 Compose/Celery、未做浏览器人工点测。
- 用户工作区中既有 Excel 修改未触碰。
