# CHG-20261021-006 本机报告 HTTP 字节核对

## 问题与决策

已有四文件离线工具需要手工保存四份响应；上一轮页面只证明下载请求发起，尚不能确认服务端实际交付字节。决定新增只读本机 API 核对命令，复用离线校验器，自动获取同一 Run 的四份响应并检查披露版 HTTP 摘要头。仅允许 localhost/127.0.0.1 HTTP API，密码从环境变量或隐藏输入读取，临时文件自动清理。实际执行者：Codex。

## 修改内容与位置

- `tools/verify_live_report_delivery.py`：登录、唯一 Run 前缀匹配、四份 HTTP 响应获取、HTML 类型与摘要头校验、临时目录调用既有四文件校验器；只输出摘要和字节数。
- `backend/tests/test_live_report_delivery.py`：成功、非本机 URL、重复前缀及响应头摘要冲突反例。
- `docs/REPORT_DELIVERY_VERIFICATION.md`：用法、证据边界及一次本机实测结果。
- `docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/CHANGE_INDEX.md`、A/B/C/D 四责任包：同步验收状态和实际执行者。

## 验证与边界

Mac 后端全量 **245 passed**，一条第三方弃用警告；本轮未改前端，未重跑前端测试或重新部署服务。用本机现有管理员测试账号只读核对已有 BaoStock 报告 `170ef350-457b-4684-a2c8-7dab5f6275cf`：`verified=true`、`http_checked=true`、原归档 24,387 字节、披露版 24,941 字节、原归档 SHA-256 `be27976793a42becd9c63ac7f069665947dc7fb700cb4a63c8b7257e62801d33`、数据 SHA-256 `958e7bdcd5f6269d4e9630f586b91814b40019c043d610b344bd7d5ac381b652`、风险段落 1 个。脚本没有输出令牌或报告正文，没有写入主栈数据。

此证据只验证 API 响应和四元数据一致性，不证明浏览器实际保存、真实行情、许可、因子研究正确性或 Windows 环境。连续新数据浏览器流程及队长本人产品实测仍待完成。
