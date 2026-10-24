# CHG-20261019-001 JSON 快照格式标识

## 问题与决策

JSON 快照已通过真实浏览器落盘验收，但仅有研究数据字段，离线脚本难以确认文件格式及未来字段演进版本。决定在原有顶层结构增加客户端导出元数据 `export_format` 与 `export_schema_version`，保持原有对比字段位置不变，不重新请求服务端、不改变研究结果。

## 修改位置与验证

- `frontend/src/comparison-download.ts`：序列化时加入固定格式名 `factorlab-comparison` 和版本 `1`。
- `frontend/tests/comparison-download.test.ts`：验证原始结果字段保留、格式字段存在且传入对象不被修改。
- `docs/EXPERIMENT_COMPARISON.md`：说明版本字段仅属于客户端文件格式。

前端 29 项测试通过，生产构建成功。本轮未重新进行浏览器下载；CHG-20261018-018 的浏览器证据针对加入格式标识前的 JSON 文件，不能冒充本版文件的落盘证据。实际执行者：Codex。
