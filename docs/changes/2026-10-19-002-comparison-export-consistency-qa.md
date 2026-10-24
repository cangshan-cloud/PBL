# CHG-20261019-002 对比导出跨格式一致性与新版 JSON 浏览器复测

## 问题与决策

CSV、HTML 和页面 JSON 源于同一对比结果，但此前自动化只验证各自部分字段，缺少同一组任务的身份、IC 与风险提示交叉核对；CHG-20261019-001 新增 JSON 格式标识后也未实际下载。决定扩展隔离 HTTP 旅程并复测浏览器落盘，不改变产品接口或研究算法。

## 修改位置

- `backend/tests/test_api_journey.py`：同一次研究对比中，以 API JSON 为源，逐任务核对 CSV 的完整 Run ID、完整数据版本 ID、IC 均值与共同日期 IC，以及 HTML 的完整身份和四位小数 IC；逐条核对风险提示在 CSV/HTML 中保留。
- `frontend/src/comparison-download.ts`、`frontend/src/main.tsx`：本轮只验既有 JSON 下载路径，没有修改。
- `docs/CHANGE_INDEX.md` 和 A/B/C/D 四责任包：记录验证与边界。

## 验证

后端全量 `python -m unittest discover -s backend/tests` 共 213 项通过。

定向 HTTP 旅程通过。隔离本机栈中用研究员账号运行 20 日动量与 5 日反转，生成对比，页面显示共同 IC/分组日期各 99、两条口径警告。最新版 JSON 浏览器下载实际落盘至 `/Users/judai/Downloads/factorlab-comparison-8b440291-c6f01c36.json`，6239 字节，可解析；`export_format` 为 `factorlab-comparison`、`export_schema_version` 为 `1`，首项与 `baseline_run_id` 均为完整 `8b440291-b3d6-43b9-808c-d8c7c8b42c4c`，第二项完整 ID 为 `c6f01c36-04e6-4b89-bd0f-1a6c5209b5cf`，两项完整数据版本 ID 均为 `f72bf2e6-c687-4aaa-942a-144eb6e31aee`。

首个应用内浏览器标签登录仅到 OPTIONS，页面报 `Failed to fetch`；新标签重试成功，后续路径通过。该偶发现象未定位根因，不应宣称已修复。本轮浏览器仅下载新版 JSON；CSV/HTML 由同源隔离 HTTP 测试核对，真实浏览器下载证据仍见 CHG-20261018-015。演示数据不代表真实 A 股样本、其他浏览器或 Windows 验收。下载文件保留在用户 Downloads。实际执行者：Codex。
