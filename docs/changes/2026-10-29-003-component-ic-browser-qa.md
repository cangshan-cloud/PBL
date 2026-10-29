# CHG-20261029-003 成分同样本 IC 的隔离浏览器验收

## 问题与决策

上一轮完成计算、结构化结果和前端展示，但没有让当前代码经过真实 Web、API、Celery Worker 与归档报告页面。决定复用已预检的隔离 Mac/OrbStack 五服务，在真实私有历史包上提交新 Run，核对工作台和同 Run 报告，再执行 HTTP V2 审计与窄屏检查。旧归档任务未能经现有工作台入口重新载入，明确保留为未做浏览器实测。实际执行者：Codex。

## 修改内容与对应位置

| 修改 | 位置 | 原因 |
| --- | --- | --- |
| 新 Run、页面、报告、HTTP 复现及隔离栈收尾证据 | `docs/HISTORICAL_COMPONENT_IC_BROWSER_QA_2026-10-29.md` | 补齐真实异步与浏览器路径 |
| 前轮验收的后续链接 | `docs/HISTORICAL_COMPONENT_IC_QA_2026-10-29.md` | 保留原验证状态，指向新增证据 |
| 总索引及 A/B/C/D 责任包 | `docs/CHANGE_INDEX.md`、`docs/member-deliverables/` | 同步团队验收材料 |

无应用代码、测试或配置文件修改。隔离数据库新增一个 Run；主 `fbl` 服务和用户修改的分工 Excel 未更改。

## 验证与未决事项

浏览器新 Run `9bbb1f11-548d-423c-a56c-ced6eb70d545` 成功，工作台和报告均显示四项成分 IC/Rank IC 与各 242/242 日期。严格 HTTP V2 整包、结果、报告校验和 72,366 条观测审计通过；375 px 页面无整页横向溢出，控制台 0 error/0 warning。隔离项目 `down` 后主 `fbl` 仍 `running(5)`。旧任务缺字段提示尚未浏览器实测；队长人工验收、Windows 与来源授权核验仍未进行。台账和链接检查随本次提交执行。
