# CHG-20261018-002：退出登录后的只读资源响应隔离

## 背景与决策

研究轮询和实验对比已分别有旧请求失效机制，但任务、报告、数据集、因子、总览和用户列表的只读加载仍直接把晚到响应写入 React 状态。若账号 A 退出、账号 B 登录，A 的慢请求可能覆盖 B 页面资源；旧请求失败也可能把错误提示带到新会话。

决定为这六类列表／总览加载统一捕获前端认证会话序号。退出登录时递增序号；请求完成后仅当前序号可以发布结果，旧错误也不再抛给页面提示。它只保护前端状态，不替代后端身份验证、权限过滤，也不声称中止已发出的网络请求。

## 修改位置

| 内容 | 位置 |
| --- | --- |
| 旧会话成功响应和错误均返回空结果；当前会话错误仍抛出 | `frontend/src/auth-resource.ts::loadForCurrentSession` |
| 六类资源加载接入会话检查，退出时使旧会话失效 | `frontend/src/main.tsx::loadDatasets`、`loadFactors`、`loadDashboard`、`loadUsers`、`loadTasks`、`loadReports`、`logout` |
| 当前成功、旧响应晚到、旧错误晚到、当前错误四类回归 | `frontend/tests/auth-resource.test.ts`、`frontend/package.json` |
| 决策及责任包 | 本文件、`docs/CHANGE_INDEX.md`、`docs/member-deliverables/` |

## 验证与边界

- Mac 本机前端 20 项测试和生产构建通过；本轮未修改后端或持久化数据。
- 只覆盖所列六类只读资源加载。上传、发布等写入操作和各页面独立详情请求仍有各自的生命周期；不把本轮表述为“全前端请求均已取消或隔离”。
- 未做浏览器账号切换、Compose/Celery、Windows 或真实行情的新验证。实际执行者：Codex；四人材料为代执行记录，非成员本人签收。
