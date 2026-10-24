# CHG-20261019-008 对比数据指纹的浏览器下载联验

## 问题与决策

CHG-20261019-007 已在测试和私有样本脚本中贯通数据版本 SHA-256，但尚未验收页面展示及同一组浏览器下载文件。决定在隔离的 Mac 本地栈中实际运行两条演示研究，生成对比并下载 JSON、CSV、HTML，再用只读离线校验器核对；本轮只补验收证据，不改产品逻辑。Playwright CLI 的离线依赖缓存缺失，故使用应用内浏览器执行真实交互。

## 修改与代码位置

- 产品代码无修改。被验收路径：`backend/app/services/comparisons.py`（对比对象、CSV、HTML 数据哈希）、`frontend/src/main.tsx`（页面指纹及下载按钮）、`frontend/src/comparison-download.ts`（JSON 快照）、`tools/verify_comparison_exports.py`（三格式只读联验）。
- 本记录、`docs/CHANGE_INDEX.md` 与 A/B/C/D 四责任包增加本轮证据和边界。实际执行者：Codex。

## 实测结果

使用临时 SQLite/Data Root、内联任务执行和本地 Vite 栈，研究员账号运行 20 日动量与 5 日反转，均成功。对比页“实际研究口径”两行均显示演示数据完整 SHA-256 `c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e`，与项目演示数据预期指纹一致。按动量为基准下载同一对比的三份实际浏览器文件：

- `/Users/judai/Downloads/factorlab-comparison-574fb532-39db2b5d.json`
- `/Users/judai/Downloads/factorlab-comparison-574fb532-39db2b5d.csv`
- `/Users/judai/Downloads/factorlab-comparison-574fb532-39db2b5d.html`

`tools/verify_comparison_exports.py` 对上述三文件返回 `run_count=2`、`warning_count=2`、`csv_verified=true`、`html_verified=true`。两条警告为 IC 日期和可分组日期集合不同，原始收益未重新按交集计算。三文件保留在 Downloads 供本机复核；临时服务与数据目录在本轮结束后清理。

## 验收边界

这是演示数据的浏览器联验，不是私有真实行情文件的浏览器验收，也未覆盖 Windows。离线工具验证导出之间一致性与字段形态，不独立复算因子公式、不验证来源许可或未来表现。
