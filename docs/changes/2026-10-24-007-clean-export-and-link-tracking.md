# CHG-20261024-007 干净导出复现与证据链接跟踪修正

## 问题与决策

从提交导出不含本机未提交文件的副本后，发现两张位于 `output/playwright/` 的旧图实际上已被 Git 跟踪：目录后来加入忽略规则，并不使历史已跟踪文件消失。原文档检查器按目录一律标为 `LOCAL_ONLY`，误报两处；另有一份未入库的报告 HTML 确实不可移植。决定以 Git 索引判断可分发文件，源码归档无 `.git` 时以归档内文件存在性判断；对未入库 HTML 只保留明确的本机路径说明，不提供失效下载链接。实际执行者：Codex。

## 修改内容与位置

- `tools/check_document_links.py::_tracked_files`、`audit`：读取 Git 跟踪路径；已跟踪的忽略目录文件视为可分发，未跟踪的非本地证据目标报错。无 `.git` 的干净归档按导出后文件存在性核验。
- `backend/tests/test_document_links.py::test_tracked_ignored_file_is_portable_but_untracked_file_is_not`：覆盖历史已跟踪图片与新未跟踪图片的不同结论。
- `docs/MAC_SYMBOL_ADJ_GAP_BROWSER_RUN_2026-10-23.md`：下载 HTML 改为明确的本机留存说明，不再提供克隆后失效的链接。
- `docs/RELEASE_READINESS_2026-10-24.md`、`docs/CHANGE_INDEX.md`、A/B/C/D 四责任包：更新复现与证据口径。

## 验证与边界

以 `git archive HEAD` 导出独立副本并运行旧版链接/台账检查；基础 `docker compose config --quiet` 通过。隔离 QA 覆盖配置在未设置 `FACTORLAB_QA_RUNTIME_DIR` 时拒绝解析，这是预期的写入隔离保护，不代表基础配置故障。修正后当前工作树链接扫描 907 个相对链接、0 断链、0 本地专属链接；后端全量 266 项（含新增单测）通过。提交后还需在更新后的干净归档及远端 CI 复核。此轮未启动容器、未改变任何数据卷，也未检查队长本人产品操作。
