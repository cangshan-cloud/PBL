# CHG-20261016-025：当前浏览器回归与演示 CSV 跨平台检出

- 日期：2026-10-16
- 类型：产品验收、输入展示修复、跨平台 CI 排查
- 状态：Mac 浏览器和本机回归通过；Windows CI 修复待新提交核对
- 关联提交：与本记录同次提交

## 背景与决策过程

最近三轮前端可靠性修复只有纯函数和构建证据，尚未在当前浏览器点测。实测非法分组时发现未运行卡片显示 `Q0 − Q1`，虽已阻止提交，仍可能误导研究人员，因此无效分组标签改为中性占位符。同期核对 GitHub Actions 发现最近四个提交的 Windows 作业失败而 Ubuntu 成功；匿名作业日志不可读。比较最后绿色提交与最早失败提交，后者新增演示 CSV 原始字节摘要断言；决定通过 Git 属性固定该 CSV 在 Windows 为 LF，而不弱化摘要断言或跳过 Windows 测试。此归因必须以新提交的 CI 结果验证。

## 修改内容与位置

| 内容 | 位置 |
| --- | --- |
| 无效分组标签显示 `—` 而非 `Q0 − Q1`／`QNaN − Q1` | `frontend/src/research-config.ts::longShortGroupLabel` |
| 增加 0 与 `NaN` 断言 | `frontend/tests/research-config.test.ts` |
| 演示 CSV 在跨平台检出时固定 LF | `.gitattributes` |
| 浏览器步骤、Run ID、CI 排查、局限及本机测试 | `docs/CURRENT_BROWSER_AND_CI_QA_2026-10-16.md` |
| 追溯索引与四责任包 | 本文件、`docs/CHANGE_INDEX.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/member-deliverables/` |

## 验证与风险

Mac 浏览器两条合成 Run 成功；任务和报告的常规切换正确，控制台错误／警告均 0。前端 13 项、构建、后端 191 项和黄金验算通过；`git check-attr` 显示演示 CSV 为 `text eol=lf`。浏览器没有人为制造慢响应；这不是 Celery/Compose、Windows 浏览器或正式演示。Windows CI 故障原因仍为基于时间线与代码的推断，推送后必须核对同一提交的 Ubuntu/Windows 作业。若仍失败，不可沿用推断，应获取登录后的作业日志或构造 Windows 复现。实际执行者：Codex。
