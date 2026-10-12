# CHG-20261013-003：历史沪深 300 离线不可变数据包

- 日期：2026-10-13
- 类型：implementation + evidence
- 状态：offline sealed / verified；平台注册待实现
- 关联提交：与本记录同次提交

## 决策过程

DEC-20261012-009 已确定数据包应绑定价格、交易日历、成分、交易/ST 状态及各文件哈希，运行时不得重新查询上游。上一阶段两份私域原始快照已分别验证，但平台仍无法把它们当作一个版本。先实现与数据库无关的离线封存和复验，锁定数据内容及规则；平台注册和研究执行随后接入，保留原有单 CSV 数据集路径。

## 修改内容与对应位置

- `tools/build_hs300_bundle.py::validate_sources/build_bundle`：验证全年成员与价格状态源快照、预热/标签日期、成员日覆盖和交易日历一致；复制源文件到临时目录，计算 576 个文件哈希与内容地址，拒绝覆盖同版本。
- `tools/verify_hs300_bundle.py::verify_bundle`：核对目录名、身份哈希、确切文件集合和逐文件哈希，再重跑成员、价格及跨组件语义验证。
- `backend/tests/test_hs300_bundle.py::Hs300BundleTests`：封存成功、相同 ID 拒绝覆盖、篡改拒绝。
- `docs/HS300_BUNDLE.md`：使用方式、实测哈希和限制；`docs/HS300_DATA_FEASIBILITY.md`、`docs/HS300_PRICE_STATUS.md` 更新剩余任务；`docs/CHANGE_INDEX.md` 登记本次改动。
- 原始及封存包均位于 Git 忽略的 `data/real/`，未进入公开仓库；本次未修改数据库、API 或因子计算。

## 验证与未决事项

本机包 `hs300_2024_0375298bd2c8ac52` 通过 576 文件校验和全量语义复验，清单 SHA-256 为 `29e09ea82da9c15fcd8c7ebb2d3c99fd795df82312f6e2b431301ce2efd676d5`。后端全套 94 项测试通过。尚未将包注册为平台 `DatasetVersion`，也未实现严格日历窗口、t/t+1 标签、排除审计及报告；不能以“离线包已封存”冒充课程扩展功能完成。
