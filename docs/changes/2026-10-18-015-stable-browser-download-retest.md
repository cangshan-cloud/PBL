# CHG-20261018-015 稳定隔离环境复测对比导出

## 背景与决策

此前 640px 点测中，CSV 点击只观察到 OPTIONS、没有 POST 或下载事件；前端热更新与页面重载使结果无法定性。随后已分别验证 Blob 下载生命周期和服务端 CORS 旅程。本轮不再改动产品代码，而是在保持隔离服务稳定的情况下完成真实浏览器复测，避免把自动化测试通过误写成下载通过。

## 测试范围与代码位置

- 下载触发与命名：`frontend/src/main.tsx`、`frontend/src/blob-download.ts`、`frontend/src/comparison-format.ts`。
- 导出接口与内容：`backend/app/services/comparisons.py`、`backend/app/api/research.py`；CORS 配置：`backend/app/main.py`、`backend/app/config.py`。
- 本次实际修改：仅本记录、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四份责任包；产品代码未修改。

## 复测证据

在临时 SQLite/数据目录、独立 API `127.0.0.1:18004` 和前端 `127.0.0.1:15177` 下，以研究员账号登录。依次运行 20 日动量和 5 日反转，生成双任务对比，页面显示共同有效 IC 日及共同多空分组日均为 99，并提示两任务实际有效日期集合不同。

应用内浏览器点击两种导出后，下载事件均返回真实落盘路径：

- CSV：`/Users/judai/Downloads/factorlab-comparison-1c626502-b631c15f.csv`，3.3 KB。
- HTML：`/Users/judai/Downloads/factorlab-comparison-1c626502-b631c15f.html`，7.3 KB。

CSV 首行包含 `dataset_version_id`、`run_id`、共同日期指标和基准差值；两行任务均有完整 Run ID 与相同的完整数据版本 ID。HTML 的任务溯源表含完整 Run ID、数据版本 ID、代码版本，并披露“存在口径差异，请谨慎解释”。因此本轮可确认浏览器下载链路成功。此前仅 OPTIONS 的单次现象在本轮未复现，不能据此认定其根因或证明所有环境绝无偶发问题。下载文件保留在用户 Downloads，未擅自删除。

## 验收边界

这是 Mac 单机隔离栈、演示数据与研究员账号的复测；不代表真实 A 股样本、Windows 部署或所有浏览器均已验收。实际执行者：Codex。
