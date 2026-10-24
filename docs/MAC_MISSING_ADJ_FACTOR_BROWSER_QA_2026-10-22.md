# Mac 隔离缺少复权乘数列浏览器验收（2026-10-22）

## 环境与合成数据

复用专用项目 `factorlab-browser-qa-1022-price` 及运行目录 `/private/tmp/factorlab-browser-qa-1022-price-w88WTF`；启动前隔离 Compose 预检 PASS，再构建并启动 Web/API/Worker/DB/Redis。管理员在容器化 Web 页面导入并发布 3 股、4 日、12 行的合成 CSV `no-adj-qa-20261022.csv`，仅含 `trade_date,symbol,close,pe`，不含 `adj_factor`。新增版本 `b98cc176-6003-4fee-b274-a9d3787e14a5`（`no_adj_column_qa_1022 / 20261022.110441.704593`），保留在专用隔离数据库卷中，不在主栈。实际执行者：Codex。

## 页面与接口结果

研究员登录后总览显示 3 个已发布版本、1 条任务、1 份报告。研究工作台选中新合成版本并使用 `close × adj_factor` 时，单因子和等权多因子均显示“当前数据版本缺少 adj_factor 列”提示，`运行研究` 按钮禁用；改回导入 `close` 后，提示消失且按钮恢复。[容器页面截图](../outputs/qa-2026-10-22/container-missing-adj-factor-2026-10-22.png)记录等权多因子禁用状态；Playwright 快照记录了单因子与恢复状态。

对同一隔离 API 直接提交单因子和等权多因子 `factor_adjusted` 请求，均返回 HTTP 400，正文为 `dataset is missing adj_factor required by factor_adjusted price basis`。第一次接口核对命令依赖未安装的 `jq`，因此未取得令牌而返回 401；更换本机 Python 解析登录响应后重试，才得到上述有效 400 证据。页面返回总览时仍为 3 版、1 任务、1 报告，未生成失败任务。

## 收尾与边界

浏览器会话关闭，精确隔离项目执行 `down`（未用 `-v`）；容器及网络移除，专用卷和运行目录保留，主栈未执行 Compose 操作。合成 CSV 只测试软件行为，不认证真实行情、复权定义、因子指标或可交易收益；未运行新研究任务，也不替代队长本人产品实测。见 [CHG-20261022-012](changes/2026-10-22-012-missing-adj-factor-container-qa.md)。
