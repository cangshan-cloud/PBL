# CHG-20261024-006 发布提交跨平台 CI 复核

## 问题与决策

先前因接口限制把远端 CI 标为待核实。现通过 GitHub Actions 页面定位到运行 ID，并用已连接的 GitHub 作业接口读取逐作业结果。决定将发布提交的 CI 状态改为“已核实通过”，同时明确这不等于 Windows 实机部署或队长本人产品验收。实际执行者：Codex。

## 修改内容与位置

- `docs/RELEASE_READINESS_2026-10-24.md`：记录 #107、#108 的提交、作业和检查结果，替换此前“远端 CI 未核实”的当前状态；保留历史过程说明。
- `docs/CHANGE_INDEX.md`：登记本次复核及决策。
- `docs/member-deliverables/A_系统架构与集成验收.md`、`B_数据工程与质量验收.md`、`C_因子研究与指标验证.md`、`D_产品测试与展示验收.md`：同步四责任包的 CI 证据和验收边界。
- 无业务代码修改。

## 验证与边界

- [#107](https://github.com/cangshan-cloud/PBL/actions/runs/40071019023) 对应 `1dc0f88`：Ubuntu、Windows 两个 `Verify` 作业均 `completed/success`。
- [#108](https://github.com/cangshan-cloud/PBL/actions/runs/40071138703) 对应 `7aef107`：Ubuntu、Windows 两个 `Verify` 作业均 `completed/success`；逐步骤的后端测试、变更台账、文档链接、黄金结果、前端测试与构建均为 `success`。
- 本轮是远端只读复核，未重跑、修改或取消工作流。CI 的 Windows runner 只证明自动化在该环境通过，不证明 Windows 本地容器部署、浏览器操作或队长实测。此记录后续提交自身的 CI 需另行核对。
