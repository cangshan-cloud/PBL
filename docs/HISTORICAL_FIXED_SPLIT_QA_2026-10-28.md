# 历史研究固定 7 月切分开发与验收（2026-10-28）

实际执行者：Codex。历史 2024 沪深300研究现在可选固定 `validation_start_date=2024-07-01`。该日期是预设研究口径，不允许通过历史接口改为其他日期；系统按信号日切分并隔离其前最后一个有观测的信号日。全区间原始指标、分组和多空序列仍保留。页面勾选状态进入配置键，切换后旧 Run 结果不会冒充当前配置；任务、报告和结论复用已有时间切分展示与规则。

后端构造 HTTP 测试覆盖不带切分与带切分两条真实执行路径、非法日期拒绝、全区间指标不变、报告和结论以验证期 IC 为分档依据。历史同包复算工具识别并重算固定切分，非法历史日期在加载封存包前拒绝。前端配置测试覆盖参数、键与模式切换；未为此新增自定义日期选择或训练权重。

使用只读封存包和临时内存 SQLite 生成私有新 Run，输出仅写入 Git 忽略的 `data/real/historical_split_replay_20261028/`，没有接触主 API、Worker、Redis 或 PostgreSQL：

```bash
.venv/bin/python tools/run_isolated_historical_replay.py \
  data/real/bundles/hs300_2024_0375298bd2c8ac52/manifest.json \
  data/real/historical_split_replay_20261028 \
  --acknowledge-private-output --validation-start-date 2024-07-01
.venv/bin/python tools/verify_research_result_consistency.py \
  data/real/historical_split_replay_20261028/reproducibility.json --require-v2
```

| 检查 | 结果 |
| --- | --- |
| 新 Run | `de899971-a946-4dd8-897b-d23b8b2bf537`，成功；四因子、5 组、全年 72,366 条观测 |
| 研究期 | 2024-01-02 至 2024-06-27；34,774 条观测、116 个有效 IC 日，IC 均值 `-0.04222318267376905` |
| 隔离日 | 2024-06-28；其下一市场日标签不会进入研究期摘要 |
| 验证期 | 2024-07-01 至 2024-12-31；37,292 条观测、125 个有效 IC 日，IC 均值 `-0.02080633248161536` |
| V2 与结果 | 严格 V2 导出/报告核对及同包复算通过；逐日结果一致性检查 242 个日期通过 |
| 摘要 | `result_sha256=94c5b00dc1965fd690c311c813d9c15484a6628cfdb24212e8e934bffe89bc00`；`report_sha256=9c828b2a53140dccd51ad1b728fdaf6ea62ff251e742f776c4eaf84ed7391c24` |

这是对已取得 2024 历史数据的**回溯分段**。固定日期降低随意挑点，但本轮日期仍是在研究已进行之后加入，不能宣称真正前瞻样本外；IC 也不是可成交收益。主 Compose 栈未重建，新勾选项未在实际浏览器页面实点；队长本人及其他组员尚未人工签收。
