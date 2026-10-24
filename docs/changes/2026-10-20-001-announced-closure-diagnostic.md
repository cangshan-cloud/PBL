# CHG-20261020-001 沪深交易所公告休市工作日诊断

## 问题与决策

此前 CSV 质量检查只统计周末行，2025-01-28 等工作日公告休市行会漏报。决定首期离线封存沪、深交易所都公告的 2024–2025 年定期休市区间，仅对命中的工作日计数，并单列未覆盖年份。选择“提示而非拒绝/删行”，因为年度公告不是完整逐日交易日历，也不包含个股停牌。现有 2024 真实样本与 2025 演示数据落在首期覆盖范围；2026 年双边页面本轮未完成稳定核对，不推断开市状态。实际执行者：Codex。

## 修改内容和位置

- `backend/app/services/market_calendar.py`：版本化 2024–2025 年公告休市区间、来源链接和工作日命中函数。来源及适用边界见 `docs/MARKET_CALENDAR_SCOPE.md`。
- `backend/app/services/datasets.py::validate_csv`：质量报告加入公告休市工作日日期数/行数/最多 10 个日期、规则版本及未覆盖年份/行数；不改变输入行或原有周末统计。
- `backend/app/services/cn_csv_adapter.py::adapt_cn_stock_csv`：适配器升为 1.3.0，预览返回新诊断并提示异常及未覆盖年份。
- `frontend/src/dataset-alerts.ts`、`frontend/src/main.tsx`：数据集页与研究工作台展示新版本报告中的公告休市和覆盖范围提醒；旧报告缺字段时不虚构“零异常”。
- `backend/tests/test_datasets.py`、`backend/tests/test_cn_csv_adapter.py`、`backend/tests/test_api_journey.py`、`frontend/tests/dataset-alerts.test.ts`：命中日、复市边界、周末互斥、超范围、预览→导入质量计数一致和旧报告回归。
- `docs/CN_DATA_ADAPTER.md`、`docs/DATASET_FORMAT.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、A/B/C/D 四责任包及总索引同步说明。

## 验证与边界

- Mac 后端定向 31 项、全量 225 项和隔离 HTTP 预览→导入测试通过；前端 39 项通过、生产构建通过；`git diff --check` 通过。合成 CSV 中 2025-01-28 的两只证券计为一个公告休市工作日/两行，2025-02-01 仅计周末，2025-02-05 不计异常；2024-06-10 命中而 6 月 11 日不命中。输入行均保留。
- 本轮尚未重建 OrbStack API/Web/Worker，也未在浏览器上传新样本；此前已发布版本的质量报告不会自动回填。后续如需对既有真实版本复核，应做只读审计或独立重新导入，不可把旧报告缺字段写成“已通过”。
- 公告休市命中不等于完整交易日验证；临时休市、个股停牌、节假日公告修订和 2026 年以后的日期仍需单独核查。代码镜像和 Git 提交未在本轮发布。
