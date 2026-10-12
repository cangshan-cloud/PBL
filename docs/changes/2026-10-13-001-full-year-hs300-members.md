# CHG-20261013-001：2024 全年沪深 300 成分采集与官方边界核验

- 日期：2026-10-13
- 类型：implementation + evidence
- 状态：verified membership component; full data gate open
- 关联提交：与本记录同次提交

## 决策过程

按已确认的 10 月 31 日数据可行性闸门，优先完成历史成员源证据。前一日仅采样相邻两日和年初/年末端点，不能证明逐日覆盖及变动边界。选择可断点续采的逐日采集器和独立复验器，仍将成分数据与完整可交易性数据包严格区分。官方调整核验仅针对 2024 年 12 月定期调整，避免将一次匹配夸大为所有事件正确。

## 修改内容与对应位置

- `tools/probe_hs300_history.py::validate_calendar/normalize_members/collect`：抽出日历与成员校验，增加代码格式及 `updateDate` 非未来检查，供探针和全年采集共用。
- `tools/fetch_hs300_members.py::collect_with_checkpoints/write_atomic/main`：逐交易日采集、断点校验续采、原子写入、封存清单与每日哈希；拒绝重复封存及不兼容目录。
- `tools/verify_hs300_members.py::verify_snapshot`：重算顶层与每日哈希、核对日历及 300 人名单、汇总查询日变化。
- `tools/verify_hs300_official_2024.py::verify_official_boundary`：将 2024 年 11 月中证指数官方附件中的沪深 300 调整名单手工转录为可复核代码集合，与 12 月 13 日/16 日源数据差集逐只比较。
- `backend/tests/test_hs300_probe.py`：增加封存拒改、续采、篡改检测、边界变化测试。
- `docs/HS300_DATA_FEASIBILITY.md`：记录全年数据量、哈希、官方对照来源和剩余限制；`docs/CHANGE_INDEX.md` 增加本条。
- 原始 `data/real/hs300_members_2024/` 留在本机且被 Git 忽略，未推送；未修改研究计算路径或数据库。

## 验证结果与未决事项

真实 BaoStock 0.9.4 全年查询 242 交易日、72,600 成分行；完整性复验通过，仅发现 6 月 17 日 12 出/12 入和 12 月 16 日 16 出/16 入。12 月名单与[中证指数官方调整附件](https://oss-ch.csindex.com.cn/notice/20241129172348-%E9%99%84%E4%BB%B6%EF%BC%9A%E9%83%A8%E5%88%86%E6%8C%87%E6%95%B0%E6%A0%B7%E6%9C%AC%E8%B0%83%E6%95%B4%E5%90%8D%E5%8D%95.pdf)逐只相符；日期依据[官方编制方案](https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300_Index_Methodology_cn.pdf)推定。后端 88 项测试通过。价格、停牌/ST 状态、完整不可变数据包和研究路径尚未实现，完整数据闸门仍开放。
