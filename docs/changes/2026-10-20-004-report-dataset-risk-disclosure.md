# CHG-20261020-004 研究报告的数据风险披露

## 问题与决策

数据页与研究页已披露旧合成演示版本的交易日历问题，但报告中心只显示数据版本号；旧报告可能脱离数据页被误读。决定在报告列表 API 提供不可变数据版本 ID 与 SHA-256，由前端精确绑定当前可见的数据版本并在预览外提示；不修改既有归档 HTML 或其校验和。新生成的内置演示数据报告直接写入合成数据限制。实际执行者：Codex。

## 修改内容与位置

- `backend/app/services/reports.py::list_reports`、`backend/app/schemas.py::ReportSummaryResponse`：报告索引增加 `dataset_version_id` 和 `dataset_checksum_sha256`，区分同名版本。
- `frontend/src/dataset-alerts.ts::reportDatasetByIdentity`、`frontend/src/main.tsx` 报告中心：按 ID 与 SHA 双重匹配；精确已知演示版显示合成行情限制，含周末行的版本显示复核提示。旧 HTML 按原校验和下载，不注入新文案。
- `backend/app/services/reports.py::build_report_html`：仅新生成且来源标记为 `bundled_demo` 的 `demo_daily` 报告增加合成数据限制。
- `backend/tests/test_reports.py`、`frontend/tests/dataset-alerts.test.ts`：验证身份字段、来源限定、ID/摘要不匹配时不错误套用提示。

## 验证与边界

Mac 后端全量 229 项、前端 41 项、前端生产构建与 `git diff --check` 通过。确认 27 个任务均成功后，定向替换 API、Worker、Web；DB、Redis 与数据卷保留。镜像 SHA-256 分别为 API `1089189abc985b8bb78ff9b00e1bf1f953b9262d64b571412c738ba982487ff1`、Worker `9775110d7dab10334d9a654a5a2774698d94fa558ba57886ff3e9c6882e4d3b0`、Web `a2d3377258ae4350676b643f38dc9f615c0e2ba9f87dca4f3ff17e21fe43b5d3`。

主栈管理员浏览器：默认旧演示报告在预览外显示合成数据限制，切换到 BaoStock 真实样本报告后该提示消失。截图 `outputs/qa-2026-10-20/report-dataset-disclosure.png`。更新后仍有 3 个数据版本、27 个任务、27 个报告 HTML 产物。旧归档 HTML 不变，若脱离平台单独分享旧文件，仍需随附本次数据审计说明。前端匹配不到已加载数据版本时不猜测来源。未做 Windows 验收；未为验证新报告内置提示而额外创建 Run，该部分由单测覆盖。
