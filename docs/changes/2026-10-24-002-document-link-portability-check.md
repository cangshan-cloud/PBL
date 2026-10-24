# CHG-20261024-002 文档证据链接可移植性检查

## 问题与决策

发布清单指出部分文档引用 Git 忽略目录，但此前只有文本搜索结果，无法区分普通提及和真实 Markdown 链接，也无法阻止新的仓库内断链。决定增加只读链接审计：缺失的仓库相对目标使检查失败；指向明确本地私有目录的链接单独列为 `LOCAL_ONLY`，默认暂不导致 CI 失败，严格模式可用于收尾。实际执行者：Codex。

## 修改内容与位置

- `tools/check_document_links.py::audit`：扫描 `docs/**/*.md` 的相对链接，解析 URL 编码与路径，识别仓库外逃逸、缺失目标和本地忽略目录。
- `backend/tests/test_document_links.py`：覆盖正常、缺失、本地私有和逃逸链接。
- `.github/workflows/ci.yml`：在 Ubuntu/Windows CI 中执行文档链接检查。
- `docs/RELEASE_READINESS_2026-10-24.md`：把原来“21 份文档提及”细化为真实可点击本地证据链接数量与边界。
- `docs/CHANGE_INDEX.md`、A/B/C/D 四责任包：同步决策与核验。

## 验证与边界

本机扫描 883 个仓库相对 Markdown 链接：可分发目标缺失 0，指向本地忽略目录的链接 11；后端全量 265 项（含新增两项）通过。检查只覆盖标准 Markdown 链接，不解析纯文本路径、HTML 标签或动态生成路径；`LOCAL_ONLY` 不等于文件适合公开分发。远端 CI 尚待提交后验证。
