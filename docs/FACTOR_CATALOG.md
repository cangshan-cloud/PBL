# 内置因子库

## 1. 首期范围

课程验收版提供六个可执行的日频截面因子。因子值使用交易日 `t` 已知的数据形成，统一使用 `t+1` 收盘到收盘收益进行检验，避免使用未来数据。

| 因子标识 | 名称 | 公式 | 默认窗口 | 必需研究字段 |
| --- | --- | --- | --- | --- |
| `momentum_20d` | 20日动量 | `close(t) / close(t-N) - 1` | 20日 | `close` |
| `reversal_5d` | 5日反转 | `-(close(t) / close(t-N) - 1)` | 5日 | `close` |
| `volatility_20d` | 20日波动率 | `std(daily_return, N)` | 20日 | `close` |
| `turnover_20d` | 20日平均换手率 | `mean(turnover_rate, N)` | 20日 | `turnover_rate` |
| `market_cap` | 总市值 | `total_mv(t)` | 当日截面 | `total_mv` |
| `pe` | 市盈率 | `pe(t)` | 当日截面 | `pe` |

所有因子还需要 `trade_date`、`symbol` 和 `close`；其中 `close` 同时用于计算下一日收益。

## 2. 统一执行规则

- 因子元数据与计算函数登记在同一注册表，API、数据库目录和任务执行器使用相同定义。
- 创建实验时固定因子键、因子版本、数据版本、窗口参数、分组数和代码版本。
- 窗口型因子允许设置 2—120 个交易日；截面型因子不接收窗口参数。
- 数据集缺少因子所需字段时，任务提交返回 HTTP 400，并明确列出缺失字段。
- 数据历史不足、文件被篡改或计算异常时，任务进入 `failed` 状态并保留错误摘要。
- 单因子检验支持可开关的 MAD 去极值和截面 Z-score 标准化。
- 当前尚未实现行业、市值中性化；报告中不得声称已经完成。

## 3. 数据适配说明

仓库自带的 `demo_daily` 0.2.0 演示数据包含全部必需字段，可直接演示六个内置因子。数据为可复现的合成数据，仅用于软件流程验收，不得用于投资结论。完整 CSV 规范见 [DATASET_FORMAT.md](DATASET_FORMAT.md)。

## 4. 接口

登录后调用 `GET /api/v1/factors` 获取六个因子的名称、分类、版本、公式、字段依赖和默认窗口。创建任务时在 `POST /api/v1/research/tasks` 请求体传入因子标识，例如：

```json
{
  "factor": "reversal_5d",
  "dataset_version_id": "<数据版本ID>",
  "lookback": 5,
  "groups": 5
}
```
