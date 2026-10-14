# CHG-20261014-003：历史研究逐日与无标签审计 CSV 导出

- 日期：2026-10-14
- 类型：feature + docs
- 状态：implemented
- 关联提交：与本记录同次提交

## 背景与目标

历史研究网页目前只展示四因子审计汇总。逐日排除计数和无标签信号虽然保存在任务结果与复现 JSON 中，但团队成员难以用常见表格工具独立检查。目标是对成功任务提供不改变计算口径的明细导出。

## 决策过程

考虑前端直接从任务 JSON 拼 CSV，以及后端按已保存审计生成 CSV。选后端：保证下载、角色权限和列结构一致，也避免前端复制审计解释逻辑。使用两个文件而非混合表，因为逐日汇总与逐证券异常的粒度不同。只从现存 metrics 产物读取，不重新加载私有行情，不改变因子计算、报告或数据库结构。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 生成 UTF-8 BOM 的逐日及无标签 CSV | `backend/app/services/historical_audit.py::historical_audit_csv` | 稳定列头，逐日缺失计数写 0，空明细保留表头 |
| 下载路由沿用任务访问控制，拒绝未完成或非历史任务 | `backend/app/main.py::download_historical_audit` | 研究员不能下载他人任务 |
| 在历史审计卡片增加两个下载按钮 | `frontend/src/main.tsx::downloadHistoricalAudit` 及历史审计卡片 | 无须手动处理 JSON |
| 覆盖状态、权限、两类 CSV 与无效表名 | `backend/tests/test_api_journey.py::test_historical_audit_csv_requires_owner_and_completed_historical_run` | 防止路由与权限回归 |
| 更新当前状态与导出说明 | `docs/HS300_BUNDLE.md` 的“状态”“使用边界”“审计 CSV 导出” | 消除早期阶段描述的歧义 |
| 变更登记 | `docs/CHANGE_INDEX.md` 的变更表 | 可追溯 |

## 验证与结果

- `make test`：105 项通过。
- `npm run build --prefix frontend`：TypeScript 与 Vite 构建通过。
- API 集成测试验证未登录 401、未完成 409、本人研究员 200、其他研究员 403、查看者 200、未知表 409；两种 CSV 内容与下载头通过断言。
- 未在本轮重建既有 OrbStack `fbl` 容器；现运行容器不会自动拥有新路由。私有历史包上的新 CSV 下载未做浏览器实测。

## 风险、回退与未决事项

导出的是任务已保存的审计快照，不是重新计算的独立核验。后续若需要在另一机器重算，仍需取得相同私有数据包与代码版本。可回退本次接口、服务和前端按钮，不涉及数据库迁移。
