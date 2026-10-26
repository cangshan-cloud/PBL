# CHG-20261026-008 多空逐日原值 CSV 导出

## 问题与决策

多空图能直观展示净值，却不方便逐日核对毛收益、换手、成本及成本后收益。决定仅导出当前 Run 已保存的 `long_short_series`，不在浏览器或服务端重算回测。完整 Run ID 随每行保存，成本参数也随行保留，便于与复现包核对。字段为比例值而非百分数；无有效分组日只保留表头。实际执行者：Codex。

## 修改内容与对应位置

- `frontend/src/long-short-export.ts`：生成 UTF-8 BOM、CRLF 的逐日 CSV，输出毛日收益/毛净值、双边换手、成本、成本后日收益/净值及单边 bps；使用共用 CSV 转义，保留已存数值的符号和精度。
- `frontend/src/main.tsx::NavChart`、`App::downloadLongShort`：在当前研究图和旧任务详情添加同源下载入口；图表本身仍显示已存净值。
- `frontend/package.json`、`frontend/tests/long-short-export.test.ts`：纳入三项单测，覆盖字段、完整 Run、负值、无分组日表头及文本公式转义。
- `docs/SINGLE_FACTOR_ANALYSIS.md`：明确字段单位、成本关系和非可成交边界。
- `docs/LONG_SHORT_CSV_BROWSER_QA_2026-10-26.md`、总索引和 A/B/C/D 四责任包：记录隔离旧 Run 下载与未测边界。

## 验证结果与边界

前端 75 项测试及构建、后端 283 项、黄金样例通过。隔离浏览器从旧成功历史 Run 下载 242 行，逐行核对 9 列、Run ID、10 bps 成本参数及毛收益－成本＝成本后收益，浏览器错误/警告均为零。未独立逐值比对复现包，也未实点研究工作台新任务入口；此导出不构成数据来源认证、策略回测或投资有效性证明。私有派生 CSV 不入库，用户修改的 Excel 保持原样。
