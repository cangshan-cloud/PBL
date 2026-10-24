# CHG-20261020-003 日历诊断主栈部署与旧版本浏览器验收

## 问题与决策

前两轮公告休市诊断和旧演示数据披露已经通过本机测试，但运行中的 OrbStack 服务仍是旧镜像。为完成可见验收，先只读核对任务状态：27 个任务均为 `SUCCESS`，无排队或运行任务；随后只替换 API、Worker、Web，保留 PostgreSQL、Redis 和数据卷。旧质量报告不回填、旧研究任务不重算，也不为浏览器验收新增数据版本。实际执行者：Codex。

## 修改内容与位置

- `docker compose build api worker web`，随后 `docker compose up -d --no-deps --force-recreate api worker web`。新镜像 SHA-256：API `377b57a394135e28de5bd0bcc5f5ade7c6f44348132ce4c7b552a4fae5de70b7`，Worker `fe46d0ad6a16035660ee1d0060a280ed7a102973e63ae726610f29d5591ddb3e`，Web `50884bf8eb6bb2b225116773a3d80f4347493a1bf73736c9e53d368f7470f5f9`。
- 浏览器实点 `frontend/src/main.tsx`、`frontend/src/dataset-alerts.ts` 既有数据页和研究页：旧数据集异常提示、精确版本合成数据告知、随选中数据版本切换的研究提示。
- 证据图：`outputs/qa-2026-10-20/calendar-dataset-disclosure.png`、`outputs/qa-2026-10-20/calendar-research-disclosure.png`。
- `docs/ORBSTACK_DEPLOYMENT.md`、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包记录本次部署和验收。无新增产品代码修改。

## 验证与结果

- 更新后五个服务运行；API、Worker、DB、Redis 均为 healthy，Web 为 Up。
- 更新后数据库仍有 3 个数据版本、27 个任务；浏览器总览显示 3 个已发布版本、27 个成功任务、27 份报告，排队和运行中均为 0。
- 数据页显示 `compose_accept_20261019` 的 1 个周末日期/2 行，以及精确匹配 `demo_daily / 0.2.0` 的 11 个公告休市工作日/220 行合成行情告知。
- 研究页选择 `compose_accept_20261019` 时显示周末风险；切换 `demo_daily / 0.2.0` 后改为合成数据告知，前者不再显示。

## 范围与限制

浏览器只读验收的是既有版本的提示，不等于新导入数据的整条预览/导入浏览器流程；新导入的公告休市质量字段已由 CHG-20261020-001 的后端/前端测试覆盖。2024–2025 公告休市区间不是完整交易所交易日历，0 命中不能证明真实交易日。未做 Windows 验收、真实收益证明或旧报告改写。
