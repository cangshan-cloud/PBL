# CHG-20261016-011：隔离技术彩排与四人验收材料预填

- 日期：2026-10-16
- 类型：acceptance evidence + team handoff
- 状态：developer rehearsal verified on Mac；individual sign-off pending
- 关联提交：与本记录同次提交

## 背景与决策过程

课程验收要求十分钟浏览器演示和 A/B/C/D 四份个人材料。原清单都是待填写模板，不能把既有自动测试当作四名成员已经完成自验。决定先做开发者可控的技术彩排：对现有 OrbStack 主栈只读预检；对当前代码另起临时 SQLite + inline API/Vite 环境，浏览器实际走角色、任务、报告和下载；保留生成文件与核对摘要。由于隔离 inline 不经过 Celery，而且自动化交互不等于 D 连续讲解计时，正式清单仍保持未勾选。四份个人材料仅预填已有证据及每人必须亲自做的步骤，保留签名与交叉复核空项。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 开发者技术彩排结果、Run 和环境边界 | `docs/DEV_REHEARSAL_2026-10-16.md` | 提供可追溯的实际证据与未验项 |
| 正式清单区分技术彩排 | `docs/FINAL_REHEARSAL_CHECKLIST.md` | 防止误勾四人验收 |
| A/B/C/D 可核对证据与个人待办 | `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md` | 降低成员填写成本，不代签 |
| 总索引 | `docs/CHANGE_INDEX.md` | 定位本次决策 |

## 验证与结果

- Mac OrbStack 主栈：宿主机 API/Web HTTP 200；只读预检通过三账号、演示数据、六因子、备用报告摘要、活跃任务及 Worker ping。
- 隔离浏览器：管理员→研究员→查看者流程通过；Run `3b0d0a4c-c38c-410b-81bd-7d159047881d` 成功；JSON/HTML 浏览器下载及独立摘要核对通过；控制台 0 错误、0 警告。
- `.venv/bin/python -m unittest discover -s backend/tests -q`：182 项通过；`npm run build --prefix frontend`、黄金验算、真实 10 股私有样本回归均通过。
- `git diff --check`：见提交前检查。

## 风险、回退与未决事项

技术彩排不是四人个人工作证明。主栈镜像早于当前提交，不据此声称本版 Celery 新任务通过；隔离浏览器使用 inline 模式，未验异步排队。浏览器生成文件在 Git 忽略目录，本机可复核但团队其他机器不会自动获得。正式演示须固定提交、核对 CI/镜像、由 D 连续计时并由 A/B/C/D 各自签收；Windows 实机仍未验。
