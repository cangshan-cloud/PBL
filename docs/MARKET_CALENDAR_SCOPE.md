# 沪深 A 股公告休市诊断（2024–2026）

本功能把沪、深交易所年度公告中共同的定期休市区间封存在代码中，仅用于 CSV 导入前后的质量提示。当前版本 `sse-szse-announced-closures-2024-2026-v2`；规则在 `backend/app/services/market_calendar.py`。来源为交易所原始公告：[上交所 2024](https://www.sse.com.cn/disclosure/dealinstruc/closed/c/c_20231226_5733941.shtml)、[深交所 2024](https://www.szse.cn/disclosure/notice/t20231226_605108.html)、[上交所 2025](https://www.sse.com.cn/disclosure/dealinstruc/closed/c/c_20241223_10767110.shtml)、[深交所 2025](https://www.szse.cn/disclosure/notice/t20241223_611283.html)、[上交所 2026](https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml)、[深交所 2026](https://www.szse.cn/disclosure/notice/general/t20251222_618087.html)。资料核对于 2026-10-20。

诊断只对 2024–2026 年的**工作日且落在公告休市区间**的行情计数，避免与已有周末行计数重复。报告分别保存受影响日期数、行数、全部命中日期和规则版本；年份不在覆盖范围内时记录未覆盖年份与行数，不把“零个命中”解释为“全部日期合规”。适配预览也展示风险和未覆盖提醒。导入不会删行或阻断发布，原始 CSV 和既有研究结果不被重写。

这不是交易所提供的完整逐日开市清单：不能排除临时休市、特殊证券停牌或源文件缺行，也不能证明其余工作日一定交易。历史已发布数据版本的质量报告不自动回填新字段；需要重新导入或另做只读审计，不能把旧报告中缺字段当成零异常。2027 年及其他年份暂不覆盖，扩年应先双边核对公告，更新规则版本并增加边界测试。旧报告的规则版本仍保持原记录，不因当前代码升级而改写。

现有主栈旧版本的只读复核结果和演示数据限制见 [2026-10-20 审计记录](MARKET_CALENDAR_AUDIT_2026-10-20.md)。
