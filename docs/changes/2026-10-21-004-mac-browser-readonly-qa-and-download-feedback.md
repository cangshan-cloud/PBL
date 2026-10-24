# CHG-20261021-004 Mac 浏览器只读验收与报告下载反馈

## 问题与决策

P3 需要从真实页面观察当前主栈，但本轮不应为验收再污染已有数据库。决定只读浏览总览、数据集、研究配置、报告预览及已有任务对比。实点发现披露版下载按钮没有页面反馈，用户难以区分“点击了”与“请求失败”。因此补充下载流程错误捕获和谨慎成功文案：仅声称已发起下载，要求在浏览器下载列表确认，不声称落盘。Playwright CLI 包装器在沙箱内启动无输出；改用应用内浏览器完成实点。实际执行者：Codex。

## 修改内容与位置

- `frontend/src/report-download.ts`：抽出按所选 Run 请求披露版和生成文件名的可测试函数，失败响应/保存异常直接抛出。
- `frontend/src/main.tsx`：报告下载按钮调用该函数；成功显示文件名和需人工确认的提示，失败显示错误，不改原归档。
- `frontend/tests/report-download.test.ts`、`frontend/package.json`：加入成功及失败分支测试到默认前端测试命令。
- `docs/MAC_BROWSER_ACCEPTANCE_2026-10-21.md`、`docs/ORBSTACK_DEPLOYMENT.md`、计划、总索引与 A/B/C/D 四责任包：记录本轮范围、证据和限制。
- 截图 `outputs/qa-2026-10-21/report-download-notice.png`：报告中心成功反馈页面。

## 验证与边界

Mac 前端 **45 passed**、后端 **242 passed**（一条第三方弃用警告），前端生产构建成功。仅重建并替换 Web，API/Worker/DB/Redis 保留；五服务运行，数据库只读计数仍为 3 个数据版本、27 个成功任务、27 份报告。Web 镜像 SHA-256 `5f399aa7ccfbde4df00cf57a00b6eac9d2d065e0101e6bd151423a972aed36f8`。浏览器复点显示 `factor-report-170ef350-disclosed.html` 下载发起提示。

本轮没有新导入或新 Run，也未独立读取浏览器下载文件；因此只证明页面交互和提示，不等于完整端到端产品验收或文件落盘证明。既有旧任务缺逐股观测产物是已提示的历史能力边界；不能用共同日期 IC 替代严格同样本 IC。Windows 未验收。
