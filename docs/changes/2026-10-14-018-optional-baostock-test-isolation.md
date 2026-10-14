# CHG-20261014-018：历史采集测试隔离可选 BaoStock 依赖

- 日期：2026-10-14
- 类型：fix
- 状态：implemented，远端 CI 待验证
- 关联提交：与本记录同次提交

## 背景与目标

提交 `8ab9252` 的公开 GitHub Actions [运行 #38538602151](https://github.com/cangshan-cloud/PBL/actions/runs/38538602151) 在 Ubuntu 和 Windows 的“Run backend tests”步骤失败。本机虚拟环境的 129 项测试通过，但额外安装了 `baostock==0.9.4`，而 CI 只安装 `backend[dev]`。历史采集单元测试调用真实封存函数，函数在清单中读取 `importlib.metadata.version("baostock")`；这使不需联网、也不应依赖可选采集包的测试受到环境影响。公开 Actions API 只提供失败步骤，未获可读的断言日志；上述是代码检查和本地复现得到的根因判断，不能冒充远端日志结论。

## 决策过程

考虑在 CI 中额外安装 BaoStock，但采集包不属于平台后端的必备运行依赖，而且单元测试传入模拟数据源，并不验证 BaoStock 本身。选择在测试中显式模拟包版本，保留真实采集时记录实际版本的生产逻辑。若远端仍失败，继续读取可用日志或在干净环境定位其他原因。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 历史成员测试在每项测试期间模拟 BaoStock 版本 | `backend/tests/test_hs300_probe.py::Hs300ProbeTests.setUp` | 不再依赖本机安装可选采集包 |
| 历史价格测试采用相同隔离 | `backend/tests/test_hs300_prices.py::Hs300PricesTests.setUp` | 保持封存清单字段测试可重复 |
| 登记本次修复 | `docs/CHANGE_INDEX.md` 对应条目 | 保留失败证据与决策 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：129 项通过。
- 在进程内令对 `baostock` 的版本查询抛出 `PackageNotFoundError`，再运行完整测试：129 项通过；历史采集相关 12 项也单独通过。
- 远端 Ubuntu/Windows CI：本记录编写时尚未重跑；不得记为通过。

## 风险、回退与未决事项

模拟版本只覆盖测试环境，不验证真实 BaoStock 采集兼容性。若后续 CI 仍失败，需按新运行结果进一步排查；不应仅凭本机通过关闭问题。
