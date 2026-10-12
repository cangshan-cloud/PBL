# 样例数据

`daily_prices.csv` 是为工程联调生成的确定性数据，不是真实证券行情，不得用于研究结论。当前快照为 `demo_daily` 0.2.0，包含 20 只虚拟股票、120 个交易日、2,400 行。字段：

| 字段 | 含义 |
| --- | --- |
| trade_date | 交易日期（周一至周五，未模拟法定节假日） |
| symbol | 虚拟证券代码 |
| open/high/low/close | 未复权开高低收价 |
| volume/amount | 成交量/成交额 |
| adj_factor | 复权因子 |
| turnover_rate | 换手率 |
| total_mv | 总市值 |
| pe | 市盈率 |

从项目根目录重新生成或校验快照：

```bash
python tools/generate_demo_dataset.py
python tools/generate_demo_dataset.py --check
```

生成器不使用随机数，相同代码在 macOS 和 Windows 上应产生相同内容。修改生成规则时必须升级数据集版本。
