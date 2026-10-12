# 项目变更与决策总索引

本索引是项目修改记录的唯一入口。从基线提交 `5d081b4` 起，每次修改项目代码、测试、配置或正式文档，都应在同一次提交中增加或更新一条 `docs/changes/` 记录，并在下表登记。记录必须同时说明**做了什么、对应位置、为何选择、验证结果和未决事项**；仅有提交说明或聊天记录不算完成。目录模板见 [`changes/TEMPLATE.md`](changes/TEMPLATE.md)。

“对应位置”使用仓库相对路径和函数／类／章节名称，必要时增加行号；行号可能随以后修改变化，路径与名称应可长期定位。纯文档改动也应写明文档章节，并标注“无代码改动”。做扩展项决策但暂不写代码时，记录为 `decision-only`；尚待用户选择的方案只能标注 `open`，不得写作已决定。

| ID | 日期 | 类型／状态 | 内容 | 记录 | 对应位置 |
| --- | --- | --- | --- | --- | --- |
| CHG-20261012-001 | 2026-10-12 | governance / implemented | 建立变更、决策记录与总索引；扩展讨论保持未决 | [记录](changes/2026-10-12-001-change-governance.md) | `docs/CHANGE_INDEX.md`、`docs/changes/TEMPLATE.md`、`README.md` |
| DEC-20261012-001 | 2026-10-12 | decision-only / open | 扩展范围第一轮 grill-me：待队长回答后继续展开依赖分支 | [记录](changes/2026-10-12-002-extension-frontier.md) | `docs/EXTENSION_OPTIONS.md`、`docs/PRD.md`、`docs/REAL_A_SHARE_SAMPLE.md`（只读依据） |

## 历史基线

`5d081b4` 及之前的提交属于本制度建立前的历史；原有 PRD、进度、真实数据验收和扩展建议分别见 [`PRD.md`](PRD.md)、[`PROJECT_STATUS_2026-10-12.md`](PROJECT_STATUS_2026-10-12.md)、[`REAL_A_SHARE_SAMPLE.md`](REAL_A_SHARE_SAMPLE.md)、[`EXTENSION_OPTIONS.md`](EXTENSION_OPTIONS.md)。这些文档和 Git 历史可供追溯，但不冒充逐次决策记录。若以后补录历史，必须明确标为“追溯补录”并说明证据来源。
