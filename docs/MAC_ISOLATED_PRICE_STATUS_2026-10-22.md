# Mac 隔离栈适配来源复权状态验收（2026-10-22）

## 环境与决策

使用 OrbStack Docker 29.4.0，专用 Compose 项目 `factorlab-browser-qa-1022-price`、端口 `127.0.0.1:18021`、运行目录 `/private/tmp/factorlab-browser-qa-1022-price-w88WTF` 和数据库卷 `factorlab-browser-qa-1022-price_postgres_data`。启动前 `tools/verify_browser_qa_compose.py` 对项目名、端口、挂载、DB/Redis 地址和独立卷返回 PASS。仅启动 DB、Redis、API、Worker，四服务均健康；未启动 Web，故本轮不是浏览器验收。实际执行者：Codex。

## 实测链路与结果

通过隔离 API 使用 3 股、4 日的**合成** `close`/`pe` 数据和单一 `adjustflag=2` 状态：适配预览确认来源状态，按原文件 SHA 绑定导入并发布，研究员提交 PE 两组任务，Celery Worker 完成。数据版本 ID `d3585c47-ff78-4ed0-b1a1-b08757f38d3e`，标准化 CSV SHA-256 `bfcfdcfc07f45d46e8e1105fda1e059431808b2526a5a77852a912c187f7fea2`；Run `0b7c11ea-d67a-416c-acf6-2b51facb4338` 状态 `success`。

报告列表绑定同一版本 ID/SHA。原归档 12,832 字节，SHA-256 `19df64e9f01ac77c01fedffa6ec85b3a0be1b573bd54c249da906853d05298c7`，与报告列表及披露响应头一致；交付副本 13,456 字节。原归档显示 `adjustflag=2（来源声明的前复权状态）` 和“价格口径：导入的 close”；交付副本保留原正文提示并增加独立披露段。交付后重读原归档，字节不变。仅输出上述身份和摘要，未保存或公开合成 CSV/报告全文。

## 收尾与限制

测试后只对精确项目执行 Compose `down`，未使用 `-v`；该项目容器和网络已移除，专用数据库卷与运行目录保留供复核，主栈未执行任何 Compose 操作。没有测浏览器文件落盘、Windows 或真实行情许可；合成 PE 字段不证明财务披露时点、因子有效性或可交易收益。见 [CHG-20261022-004](changes/2026-10-22-004-isolated-price-status-celery-qa.md)。
