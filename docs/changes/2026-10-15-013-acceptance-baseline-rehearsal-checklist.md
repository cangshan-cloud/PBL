# CHG-20261015-013：更新验收基线与最终彩排清单

- 日期：2026-10-15
- 类型：documentation + acceptance planning
- 状态：prepared; rehearsal not yet executed
- 关联提交：与本记录同次提交

## 背景与决策过程

10 月 14 日验收矩阵的本机自动测试数字停在 130 项，之后研究口径、任务可靠性与演示预检均有修改。继续用旧数字或把历史 CI 成功当作当前提交成功，会使答辩证据失真。现有十分钟剧本有步骤和简表，但缺少逐项打勾、任务/报告 ID、版本、用时和失败降级的记录字段。决定保留原文件名及历史 CI 链接，明确 10 月 15 日本机代码基线和各证据边界；新增一份默认全部未完成的彩排清单，不代替 D 的实际操作与四人署名。Windows 部署继续列为未验，未擅自扩大功能范围。

## 修改内容与对应位置

| 内容 | 位置 |
| --- | --- |
| 更新当前本机 152 项测试、黄金样例、前端构建证据，区分历史 CI 与当前提交；补研究口径变更链接和放行条件 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md` |
| 会前门槛、十分钟环节、证据字段、失败降级与个人签收空白清单 | `docs/FINAL_REHEARSAL_CHECKLIST.md` |
| 从彩排剧本和首页指向清单 | `docs/DEMO_REHEARSAL.md`、`README.md` |
| 登记本次修改 | `docs/CHANGE_INDEX.md` |

## 验证与结果

- 基线 `fffad78` 本机：`.venv/bin/python -m unittest discover -s backend/tests -q`，152 项通过。
- 同基线：`.venv/bin/python tools/verify_golden_research.py` 通过；`npm run build --prefix frontend` 通过。
- 文档相对链接和 `git diff --check` 已核对。本次只更新文档，不声称重新完成浏览器彩排、真实数据任务或 Windows 部署。

## 风险与未决事项

本轮新提交的 CI 状态需另行核对，不能沿用 `c376d4a` 的成功记录。D 的现场彩排与 A/B/C/D 各自署名仍待完成；导师若要求 Parquet/DuckDB、中性化或服务端 PDF，需要先做范围决策，当前矩阵明确列为缺口。彩排记录不得含密码或私有原始行情。
