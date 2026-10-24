# CHG-20261022-012 缺复权乘数列的容器页面与 API 实点

## 问题与决策

CHG-011 的缺列守卫通过自动化，但未在当前容器页面验收。内置演示版本实际含 `adj_factor`，不能冒充缺列反例；决定只在专用隔离数据库中导入一份明确缺列的合成 CSV，完成浏览器与 API 双侧核对，不提交新任务。实际执行者：Codex。

## 修改内容与位置

- `/private/tmp/factorlab-browser-qa-1022-price-w88WTF/no-adj-qa-20261022.csv`：隔离运行目录中的 12 行合成测试输入；不加入仓库样本或主栈。
- `docs/MAC_MISSING_ADJ_FACTOR_BROWSER_QA_2026-10-22.md`：记录版本身份、页面与 API 实点、一次无效 401 核对及收尾边界。
- `output/playwright/container-missing-adj-factor-2026-10-22.png`：等权多因子缺列提示与禁用状态截图。
- `docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、总索引及 A/B/C/D 四责任包：同步验收证据。本轮无仓库代码改动。

## 验证与边界

隔离 Compose 预检 PASS。新版本 `b98cc176-6003-4fee-b274-a9d3787e14a5` 已发布且仅在专用卷中；浏览器单因子/等权多因子均提示缺 `adj_factor` 并禁用运行，导入价恢复。直接 HTTP 两类任务请求均返回 400；前后任务和报告各 1。第一次接口命令缺 `jq` 导致 401，不作为有效结果；修正后重试的 400 才是服务端验收。浏览器与精确隔离项目已关闭，专用卷保留、主栈未动。未核验真实行情、数值研究或队长本人操作。
