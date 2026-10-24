# CHG-20261020-002 旧版本公告休市只读审计与演示数据披露

## 问题与决策

CHG-20261020-001 的日历质量字段只随新导入版本产生；直接改写旧版质量报告会破坏不可变版本与历史报告的证据链。决定提供独立只读工具，在校验存储文件 SHA-256 后重算旧普通 CSV 的公告休市诊断，不回填数据库。审计发现既有演示版本含 11 个公告休市工作日、220 行合成行情；因此对精确匹配其版本与校验和的页面输入增加合成数据限制提示，不将演示收益解释为真实市场表现。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/market_calendar_audit.py`：查询已发布数据版本、读前校验文件 SHA-256、重算质量统计，对历史封存包明确跳过，对文件损坏/缺失返回错误；不调用导入、发布或任务接口。
- `tools/audit_market_calendar.py`：CLI 入口，支持 `--dataset-id`；无数据库文件时拒绝创建 SQLite 空库。
- `backend/app/services/datasets.py::validate_csv`：保存全部公告休市命中日期，不截断为前 10 个；该清单受 2024–2025 两年公告区间约束。
- `frontend/src/dataset-alerts.ts`、`frontend/src/main.tsx`：仅对 `demo_daily / 0.2.0` 且校验和为 `c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e` 的版本显示合成日历提示；其他同名版本不套用该固定发现。
- `backend/tests/test_market_calendar_audit.py`、`frontend/tests/dataset-alerts.test.ts`：只读、旧报告不回写、损坏文件、历史包跳过、CLI 缺库与精确版本提示测试。
- `docs/MARKET_CALENDAR_AUDIT_2026-10-20.md`、`docs/MARKET_CALENDAR_SCOPE.md`、总索引及 A/B/C/D 四责任包记录事实与限制。

## 验证

- Mac 后端全量 228 项、前端 40 项、前端生产构建和 `git diff --check` 通过。
- 用新 API 镜像的一次性容器只读复核主栈 3 个已发布 CSV：3 个完成、0 个文件或解析错误；演示版本 11 个公告休市工作日/220 行，真实 BaoStock 2024 H1 为 0/0，2026-10-19 合成验收版为周末 1 日/2 行、公告休市 0/0。精确版本和 SHA 见独立审计记录。
- `docker compose build api` 仅更新本地镜像标签；运行中的 API、Worker、Web 未重建。页面新提示通过纯函数测试和构建，但尚未在 OrbStack 浏览器实点。数据库质量报告和现有研究 Run 均未回写/重算。

## 未决边界

返回码 0 仅代表文件完整且工具运行成功，不代表无休市异常。历史封存包跳过普通 CSV 审计；2026 年未覆盖。演示合成数据可用于软件功能验收，不能支持真实投资结论。下一步可部署当前代码并用浏览器只读验证提示，不需要重复导入旧版本。
