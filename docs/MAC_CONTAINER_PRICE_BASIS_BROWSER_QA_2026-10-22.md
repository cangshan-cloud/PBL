# Mac 容器化研究页价格口径浏览器验收（2026-10-22）

## 环境与步骤

复用专用项目 `factorlab-browser-qa-1022-price` 和已保留的隔离数据库卷；运行目录为 `/private/tmp/factorlab-browser-qa-1022-price-w88WTF`。启动前 `tools/verify_browser_qa_compose.py` 预检 PASS。五服务由 OrbStack Compose 启动，Web 为 CHG-008 新构建镜像，页面地址 `127.0.0.1:15121`，API 为 `127.0.0.1:18021`。Playwright CLI 在真实浏览器中使用隔离研究员测试账号登录。实际执行者：Codex。

## 实点结果

总览起始显示 2 个已发布版本、1 条研究任务、1 份报告。研究工作台选中的合成版本“隔离复权状态合成样本”带来源 `adjustflag=2`。单因子选择 `close × adj_factor` 后，页面出现“来源价格已复权或复权状态不明确，不能再次选择”的警告，`运行研究` 按钮禁用；切至等权多因子后，警告与禁用仍保持。切回导入的 `close`，警告消失、按钮恢复。返回总览后仍为 1 条任务、1 份报告；没有点击运行。

[容器化研究页截图](../outputs/qa-2026-10-22/container-price-basis-guard-2026-10-22.png)展示等权多因子错误价格口径和禁用按钮。Playwright 快照另证明单因子拦截与导入价恢复。截图/快照仅说明页面行为，不证明来源数据真实复权状态或研究指标正确。

## 收尾与限制

浏览器已关闭；精确隔离项目 `down`，未用 `-v`，其容器及网络移除，专用卷与运行目录保留。主栈未执行 Compose 操作。本轮补齐容器化 Web 的登录和页面交互验收，但没有创建新研究任务、重做报告链路、核实真实行情许可、执行 Windows 验收或替代队长本人实测。见 [CHG-20261022-009](changes/2026-10-22-009-container-price-basis-browser-qa.md)。
