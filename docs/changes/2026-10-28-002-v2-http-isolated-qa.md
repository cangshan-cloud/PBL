# CHG-20261028-002 V2 复现包隔离 HTTP 实测

## 问题与决策

前轮 V2 只在本机内存任务和离线私有包路径验证，缺少真正运行的 API 下载证据。OrbStack 恢复后决定复用已预检的隔离 QA 项目，只读下载既有成功 Run 的 JSON 与报告，避免新建任务、触碰主 `fbl` 或改写旧证据。实际执行者：Codex。

## 修改内容与对应位置

- `docs/V2_REPRO_HTTP_QA_2026-10-28.md`：记录隔离 Compose 范围、HTTP 下载、SHA-256 及保存结果审计、误报诊断与收尾。
- `docs/REPRODUCIBILITY_EXPORT_CHECK.md`：增加隔离 HTTP V2 正例与主栈未升级的界限。
- `docs/CHANGE_INDEX.md`：登记本次证据；`docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md`：分别登记对应可核查证据。无应用代码改动。

## 验证与未决事项

Compose 隔离预检通过；既有历史 Run 的 HTTP V2 JSON/HTML 下载及严格结果、整包、报告摘要核对通过，Run 身份与任务响应一致；242 日、72,366 条有效观察的保存结果内部审计通过。QA 容器已 `down`，未删除独立卷；主 `fbl` 项目未操作，仍可能导出旧版。未覆盖新任务 Celery、浏览器下载与队长人工验收。SHA-256 无密钥，不能作真实性或收益证明。
