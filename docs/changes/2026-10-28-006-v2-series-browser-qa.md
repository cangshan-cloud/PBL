# CHG-20261028-006 新历史 Run 浏览器序列 CSV 严格 V2 验收

## 问题与决策

前轮下游严格 V2 工具已有构造序列正例，但新 Celery Run 的浏览器实际序列 CSV 尚未下载。决定只在隔离 QA Web/API 上登录既有研究员，实点四个 CSV 下载，再与同 Run V2 复现 JSON 严格逐行核对；不创建任务、不触碰主栈。按 Playwright 技能使用命名会话、页面快照和 Git 忽略的浏览器产物目录。实际执行者：Codex。

## 修改内容与对应位置

- `docs/V2_SERIES_BROWSER_QA_2026-10-28.md`：记录页面操作、四文件行数/SHA-256、严格 V2 核对、控制台与隔离收尾。
- `docs/STRICT_V2_DOWNSTREAM_QA_2026-10-28.md`、`docs/SERIES_EXPORT_VERIFICATION.md`、`docs/CHANGE_INDEX.md`：追加后续正例链接，不改写前轮当时未完成的事实。
- `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md`：各自登记对应验收证据。无应用代码或测试改动。

## 验证与未决事项

四份浏览器 CSV 均由同一新 Run 下载；`verify_series_exports.py --require-v2` 对 IC 242、多空 242、组净值 1,210、逐日诊断 242 行逐值核对通过。浏览器控制台 0 error/0 warning；隔离容器关闭、独立卷保留，主 `fbl` 五服务未操作。没有队长人工签收、独立行情/公式验证或主服务 V2 升级；无密钥整包摘要也不是数字签名。
