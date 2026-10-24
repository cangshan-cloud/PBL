# 2026-10-24 发布前核对清单

## 本轮结论

当前工作树的功能回归已通过，发布候选提交 `1dc0f88` 与状态文档提交 `7aef107` 均已推送至 `origin/main`，两次远端 Ubuntu/Windows CI 均已核实通过。**这不等于 Windows 实机部署或队长本人产品验收完成。**未审查 Excel 修改仍留在本机。实际执行者：Codex。

## 已验证

- `.venv/bin/python -m unittest discover -s backend/tests -q`：263 项通过。
- `npm test --prefix frontend`：51 项通过。
- `npm run build --prefix frontend`：生产构建通过。
- `.venv/bin/python tools/verify_golden_research.py`：手算黄金样例通过。
- `python3 tools/check_change_ledger.py`：修改前 195 条索引记录、最近 33 条 CHG 与 A/B/C/D 四包关联通过；本记录入索引后应重新运行。
- `git diff --check`：无空白错误。

系统默认 `python3` 为未装项目依赖的 3.13；直接运行全量测试会出现 `fastapi`、`sqlalchemy` 缺失，不能记为产品测试失败，必须使用项目 `.venv` 或 CI 的依赖安装环境。

## 待完成的发布边界

1. 工作树含多轮代码、文档、测试和截图改动；逐项审核后分组暂存，尤其是 `outputs/progress-2026-10-16/四人分工与验收.xlsx`，不能仅凭文件名认定可发布。
2. `.playwright-cli/` 是浏览器工具自动产生的 YAML、日志、截图和临时 HTML；本轮加入忽略规则，原文件保留在本机，不纳入代码仓库。提交前应对拟提交文件做凭据和私有数据检查。
3. 文档链接检查器现按 Git 跟踪状态判断可分发性：两张 2026-10-12 页面图虽然在后来被忽略的 `output/playwright/` 目录中，却已被 Git 跟踪，干净导出副本中确实存在。真正未入库的下载 HTML 已改为本机留存文字说明，不再给出失效链接。当前链接检查结果为 0 断链、0 本地专属链接；纯文本本机路径仍是审计线索，不代表该文件已发布。
4. 截图目录 `outputs/qa-2026-10-19/` 至 `qa-2026-10-23/` 的 22 张图已逐张目视核对，拟作为发布候选。部分画面显示 BaoStock 样本名称、日期范围和统计摘要，不含可见的原始行情表或凭据；这不替代数据授权审核。真实数据原始文件仍应留在 `data/real/` 等忽略路径内，不以发布整理为由上传。
5. [CI #107](https://github.com/cangshan-cloud/PBL/actions/runs/40071019023) 对应 `1dc0f88`、[CI #108](https://github.com/cangshan-cloud/PBL/actions/runs/40071138703) 对应 `7aef107`；两次 Ubuntu/Windows 作业均 `completed/success`，后端测试、台账、链接、黄金结果、前端测试和构建步骤通过。先前 `gh` 缺失与 API 403 是取证通道限制，不是 CI 失败。队长本人产品实测及 Windows 实机部署仍未完成。

## 下一步顺序

拟提交文件的敏感信息与证据链接审查、发布提交及远端 CI 复核已完成。另从 Git 提交独立导出副本核对：文档台账与链接目标可解析，基础 `docker compose config --quiet` 通过；隔离 QA 覆盖配置未指定专用运行目录时拒绝解析，符合保护预期。下一步由队长进行本人产品实测；未审查 Excel 修改仍只在本机。若任一文件归属或授权不明确，保留本地并在清单中列为待确认，不批量加入版本库。
