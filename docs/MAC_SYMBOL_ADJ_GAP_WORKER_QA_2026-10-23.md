# Mac 隔离容器完整证券子集 Worker 验收（2026-10-23）

## 目的与环境

续接[上一轮容器页面验收](MAC_SYMBOL_ADJ_GAP_BROWSER_QA_2026-10-23.md)留下的边界：页面允许只选乘数完整的证券，但尚未在容器内实际提交。使用同一独立 Compose 项目 `factorlab-browser-qa-1022-price` 和保留的专用数据卷；预检通过后启动五服务，未操作主栈。

数据集 `symbol_adj_gap_qa_1023`，版本 ID `baaa0a6f-93ff-472f-b3dd-636818647d3f`，12 行合成数据中只有 `000002.SZ` 一行乘数为空。研究员提交 PE 单因子、`factor_adjusted`、2 组、样本 `000001.SZ,000003.SZ`，其余参数为 API 默认值。

## 实际结果

- POST `/api/v1/research/tasks` 返回 **201**；任务 `c9403c49-18d9-42cc-a5ad-24c010fba91f` 初始 `pending`，随后由 Worker 完成为 `success`、进度 100、无错误摘要。
- 可复现快照保存了数据版本、PE、调整价、2 组及两个证券代码。结果中 `coverage=6`、`resolved_symbol_count=2`，另有 `zero_observation_days=1`。这些只是 2 股 4 日合成样本的软件输出，不作统计或投资解读。
- 报告索引新增该任务，交付端点返回 HTTP 200、HTML 附件，`x-archived-report-sha256=605c632e90197ae4e1dcb193a9134c3c586e53db5cc78d22b1fa9bcbae60c0c3`；可复现快照的 `report_sha256` 相同。
- 随后提交含 `000002.SZ` 的同类调整价请求，API 返回 **400**：`selected symbols have missing adj_factor values`。最终研究员任务数 2、报告数 2，说明该拒绝请求未再创建任务。

验证结束后对专用项目执行 `down`，未使用 `-v`，专用卷和运行目录保留。直接 API 验收不等于浏览器点击“运行”验收；也未验证真实 A 股样本、Windows、复权来源或因子有效性。
