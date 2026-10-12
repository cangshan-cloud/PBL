# DEC-20261012-003：唯一大扩展主线待选择

- 日期：2026-10-12
- 类型：decision-only
- 状态：accepted
- 关联提交：初版 `824c2ca`；本次更新与索引同次提交

## 背景与依赖

前两轮已经确认数据可信度优先、最多一个大扩展、原始数据私域使用、三道时间闸门及研究主张证据标准。因此现在可以决定唯一大扩展主线；具体指数、日期区间和停牌/ST 规则需在主线选定后再问。

当前本地样本固定 10 股、没有历史成分校验，且 `total_mv` 缺失，PE 披露时点未审计。BaoStock [项目 API 文档](https://github.com/zxygithub/baostock/blob/master/docs/pythonAPI.md)列出指定日期沪深 300 成分、股票交易状态及日 K `tradestatus`/`isST`；[Tushare daily_basic 文档](https://tushare.pro/document/2?doc_id=32)列出 `total_mv`，但后者会增加数据源、权限与单位核对工作。接口存在并不保证历史覆盖、许可或无前视偏差，仍须过 10 月 31 日数据可行性闸门。

## 第三轮决策前沿

1. 是否将唯一大扩展定为“历史股票池与停牌/ST 可交易性口径”，把可靠逐日总市值、财务披露时点、中性化、IC 加权、Parquet 等后置？建议：是。队长于 2026-10-12 回复“是”，接受推荐路线。

当前仅此一项可问；数据范围、指数与规则都依赖主线选择，不在同轮预设。

## 修改内容与对应位置

本记录与 `docs/CHANGE_INDEX.md` 索引表只新增待决策材料，无代码改动。只读依据为 `docs/REAL_A_SHARE_SAMPLE.md` 真实样本限制、`tools/fetch_real_a_share_sample.py::fetch_rows` 的固定股票池、`backend/app/services/runs.py::create_research_run` 的任务参数及 `docs/EXTENSION_OPTIONS.md` 候选项。

## 验证与未决事项

已决定唯一大扩展主线，但尚未取得历史成分样本或独立验算；具体指数、日期区间、状态处理、验收阈值仍未决定。确认依据：本轮用户原话“是”；无代码改动。
