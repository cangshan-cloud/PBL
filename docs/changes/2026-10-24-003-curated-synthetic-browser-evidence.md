# CHG-20261024-003 合成样本浏览器截图定向归档

## 问题与决策

11 处可点击文档链接指向 Git 忽略目录，外部克隆无法复查。决定只迁移已经逐张目视核对的近期隔离合成样本页面截图，不批量迁移快照、日志或下载 HTML。截图未见账号密码或私有行情明细；这不是对所有元数据或历史证据的全面认证。实际执行者：Codex。

## 修改内容与位置

- `outputs/qa-2026-10-22/`、`outputs/qa-2026-10-23/`：复制 7 张原始 PNG，原文件仍在 `output/playwright/`；复制品与原件 SHA-256 一致。两张价格口径截图字节相同，保留原文件名以维持两个验收场景的定位。
- `docs/MAC_PRICE_BASIS_BROWSER_QA_2026-10-22.md`、`docs/MAC_CONTAINER_PRICE_BASIS_BROWSER_QA_2026-10-22.md`、`docs/MAC_MISSING_ADJ_FACTOR_BROWSER_QA_2026-10-22.md`、`docs/MAC_SYMBOL_ADJ_GAP_BROWSER_QA_2026-10-23.md`、`docs/MAC_SYMBOL_ADJ_GAP_BROWSER_RUN_2026-10-23.md`、`docs/MAC_CSV_PROVENANCE_BROWSER_QA_2026-10-23.md`：页面截图链接改为仓库可分发路径。
- `docs/member-deliverables/D_产品测试与展示验收.md`：对应受影响证券页面证据链接同步更新。
- `docs/RELEASE_READINESS_2026-10-24.md`、`docs/CHANGE_INDEX.md`、A/B/C/D 四责任包：更新证据边界与本轮决策。

## 验证与边界

逐张目视核对 7 张截图，SHA-256 核对复制件与原件一致。文档链接扫描为 888 个相对链接、可分发目标缺失 0；本地忽略链接由 11 降至 3。保留的 3 处是 2026-10-12 的两张图和一份报告 HTML，未经过本轮公开适宜性核对。截图证明页面可见状态，不证明私有数据授权、价格真实性、完整研究结论或队长本人验收。尚未暂存、提交、推送。
