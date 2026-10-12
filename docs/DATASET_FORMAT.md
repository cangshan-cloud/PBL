# 数据集导入格式

## 当前支持范围

当前版本支持UTF-8编码的CSV日行情文件。上传成功后先生成不可变的草稿版本，管理员确认质量报告后再发布。研究任务只能引用已发布版本。

非标准的 Tushare、BaoStock 或中文字段 CSV 可在导入前使用 A 股数据适配器，见 [CN_DATA_ADAPTER.md](CN_DATA_ADAPTER.md)。

单个文件默认不超过25MB，可通过环境变量`MAX_UPLOAD_BYTES`调整。

## 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `trade_date` | `YYYY-MM-DD` | 交易日期 |
| `symbol` | 字符串 | 证券代码，建议使用`000001.SZ`格式 |
| `close` | 正数 | 导入价格，可为未复权或已复权价格；整个数据集须保持同一口径 |

## 可选数值字段

`open`、`high`、`low`、`volume`、`amount`、`adj_factor`、`turnover_rate`、`total_mv`、`pe`。

## 当前质量规则

- 必填字段不得缺失；
- 同一证券同一交易日不得重复；
- 收盘价必须大于0；
- 成交量、成交额、换手率和总市值不得为负数；
- 最高价不得低于开盘价、收盘价或最低价；
- 最低价不得高于开盘价或收盘价；
- 日期必须采用ISO格式；
- 文件必须使用UTF-8或UTF-8 BOM编码。
- 数值必须有限，拒绝 NaN、正负无穷和浮点溢出；
- 表头不得重复，数据行列数必须与表头一致；
- 提供数值复权因子时必须大于零。任务默认直接使用 `close`；也可明确选择 `close × adj_factor`，这时所选证券的每一行都须提供有效因子。

质量报告同时记录每个字段的缺失数量和完整率，以及数值字段的有效数量、最小值、最大值和均值。可选字段允许为空，但对应因子只会使用非空且历史长度足够的观测。

数据集页面可以查看前20行预览。预览接口会重新核对文件SHA-256；文件被外部修改后返回冲突错误，不展示已经失去版本完整性的内容。单元格预览最多展示200个字符，接口最多返回100行。

## 最小示例

```csv
trade_date,symbol,open,high,low,close,volume
2025-01-02,000001.SZ,10.00,11.00,9.00,10.50,1000
2025-01-03,000001.SZ,10.50,11.20,10.00,11.00,1200
```

## API流程

1. 可选调用 `POST /api/v1/datasets/adapt/preview` 预览常见 A 股 CSV 的字段转换。
2. `POST /api/v1/datasets/import`，使用multipart表单上传`dataset_key`、`name`和`file`；需要自动适配时增加 `normalize_cn_csv=true`。
3. `GET /api/v1/datasets/{id}`查看质量报告和SHA-256校验和。
4. `POST /api/v1/datasets/{id}/publish`发布版本。
5. `GET /api/v1/datasets/{id}/preview?limit=20`查看字段和数据样例。
6. `GET /api/v1/datasets`查询全部版本。

原始文件名只作为审计信息保存；实际存储路径和文件名由服务端生成，不能由上传者控制。
