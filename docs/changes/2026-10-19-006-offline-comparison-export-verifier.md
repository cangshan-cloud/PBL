# CHG-20261019-006 实验对比导出离线校验器

## 问题与决策

单任务复现包已有离线校验工具，但对比 JSON、CSV、HTML 下载后缺少统一复核入口。决定提供只读标准库脚本：JSON 为主文件，CSV/HTML 可选；验证格式版本、基准顺序、身份、关键 IC 与风险提示的一致性，不重算研究结果，也不声称证明原始行情来源。

## 修改位置

- `tools/verify_comparison_exports.py`：新增命令行与可导入函数，核对 JSON 结构和可选 CSV/HTML；不写入任何项目数据。
- `backend/tests/test_comparison_export_verifier.py`：由实际合成研究任务生成三种导出文件，验证正例、篡改数据版本 ID 与篡改基准 ID 的拒绝行为。
- `docs/EXPERIMENT_COMPARISON.md`：说明命令、同组同顺序前提和证据边界。
- `docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包：登记本次决策与验证。

## 验证与边界

后端全量 `python -m unittest discover -s backend/tests` 共 214 项通过。

定向测试通过。脚本只读检查此前浏览器下载的 `factorlab-comparison-8b440291-c6f01c36.json`，识别两条任务、基准完整 ID、两条警告；该次未附加对应 CSV/HTML，输出中的 `csv_verified`、`html_verified` 均为 `false`，不能写成三文件实测。三文件一致性由合成任务自动测试覆盖。

本工具不提供加密签名、原始数据校验或公式独立复算；同一人同步篡改三文件仍可能通过，故只能作为一致性检查。实际执行者：Codex。
