# CHG-20261024-008 历史行情加载拒绝非有限数值

## 问题与决策

历史价格采集的成员日审计会辨识非有限数值，但平台注册/发布只核验封存文件完整性；研究加载层原先直接把字符串转为 `float`。自洽且校验和匹配的异常包可能含 `NaN`、`Infinity` 或浮点溢出值，它们会绕过 `<= 0` 等资格判断。决定在历史研究加载边界拒绝这些值，沿用空值缺失口径，不改变正常历史样本的算法。实际执行者：Codex。

## 修改内容与位置

- `backend/app/domain/historical_research.py::_bar`：解析 `close`、`turn`、`volume` 后要求有限，失败即拒绝加载。
- `backend/tests/test_historical_research.py::test_historical_bar_rejects_nonfinite_numeric_fields`：覆盖 NaN、Infinity、浮点溢出与合法空值。
- `docs/HS300_BUNDLE.md::历史包平台注册与发布`：注明运行时防线与封存前验证的不同责任。
- `docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：登记决策及本轮验收责任。

## 验证与边界

项目虚拟环境下，历史研究定向 7 项、后端全量 267 项及黄金手算核对通过。本机私有封存包只读加载成功：292 个日历交易日（含预热与次年标签日）、72,600 个成员日、328 只证券、95,776 条价格行；未修改原始数据。系统 Python 缺少 FastAPI/SQLAlchemy，首次全量命令失败，随后已用项目虚拟环境复跑成功。此防线不重新认证数据来源、成分生效时间、ST 状态或市场数据授权；无网页/容器交互变更。未经审查的团队分工 Excel 保持原样。
