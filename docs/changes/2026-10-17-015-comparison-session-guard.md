# CHG-20261017-015：实验对比请求的会话与选择隔离

## 背景与决策

实验对比提交后仍能改变勾选任务，旧响应可能晚于新选择返回，把旧组合结果显示在当前组合之下。退出登录后旧对比或导出请求也可能晚到。上一轮浏览器曾出现一次未复现的临时请求中断；本轮不把它误判为服务故障，而是处理可从前端代码确认的异步竞态。

决定给对比请求设置独立递增序号：勾选变化、再次提交或退出登录都会使旧请求失效。请求不可保证在服务端取消，但失效结果、错误和下载动作不得写入新页面。对比加载状态独立于研究等其他页面的全局加载状态，避免取消旧对比时误清空正在执行的其他操作。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 请求前后检查当前代际，晚到结果返回 `null` | `frontend/src/comparison-request.ts::resolveCurrentComparison` |
| 勾选变化、退出登录递增代际；对比及导出只发布本代结果／错误／下载 | `frontend/src/main.tsx::toggleComparisonRun`、`runComparison`、`downloadComparison`、`logout` |
| 独立的对比加载状态与按钮禁用 | `frontend/src/main.tsx` 实验对比页 |
| 当前、提交前失效、请求中失效三类时序回归 | `frontend/tests/comparison-request.test.ts`、`frontend/package.json` |
| 决策与四责任包 | 本文件、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |
| 交互行为说明 | `docs/EXPERIMENT_COMPARISON.md` |

## 验证与边界

- Mac 本机前端 16 项测试通过，生产构建通过。
- 本轮新增的是前端异步状态保护；未改后端 API、数据库和已保存 Run。
- 本轮未再启动浏览器或 Compose；时序测试使用可控 Promise，未覆盖浏览器网络断开或真实下载管理器行为。用户离开页面但未改选择／退出时，当前请求仍可能完成并写入内存；回到对比页后仍对应同一组选择。
- 实际执行者：Codex；四人责任包为代执行验收记录，不代表团队成员本人签收。
