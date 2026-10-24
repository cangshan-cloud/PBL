# CHG-20261021-001 报告披露版失败边界回归与后续计划

## 问题与决策

既有隔离 HTTP 旅程验证正常交付，但披露版接口的越权及损坏文件失败分支尚未在回归测试中单独锁定。决定补充这些测试，而不改变已上线接口：披露版必须复用原归档的权限、存在性与 SHA 校验；结构或编码不可解析时返回冲突，不输出不可信的派生文件。随后以当前事实而非旧进度文档制定课程验收优先的后续顺序。实际执行者：Codex。

## 修改内容与代码位置

- `backend/tests/test_api_journey.py`：其他研究员的资源隔离路径加入 `/api/v1/reports/{run_id}/delivery`，期望 HTTP 403。
- `backend/tests/test_reports.py`：新增披露版端点拒绝归档篡改（409）、缺失（410）、缺少可插入结构（409）、无效 UTF-8（409）的回归测试。
- `docs/DEVELOPMENT_PLAN_2026-10-21.md`：按 P0—P4 固定下一阶段工作、完成判据和边界；三次阶段汇总由队长组织，具体日期待定。
- `docs/CHANGE_INDEX.md`、A/B/C/D 独立验收材料记录本次结果。未改应用代码、API 协议、持久数据或运行容器。

## 验证与限制

Mac 定向 `test_reports.py` + `test_api_journey.py` **30 passed**；后端全量 **239 passed**（一条第三方弃用警告），前端全量 **43 passed**。`git diff --check` 通过。本轮新增的是隔离 SQLite/TestClient 和直接端点测试，不是浏览器或真实行情验收；没有重新部署，因为运行时代码未修改。
