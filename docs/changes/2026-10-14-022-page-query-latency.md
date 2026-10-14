# CHG-20261014-022：普通页面只读查询延迟基准

- 日期：2026-10-14
- 类型：tool + test + evidence
- 状态：verified on macOS OrbStack
- 关联提交：与本记录同次提交

## 背景与目标

PRD §2.3 的“普通查询不超过 2 秒”此前没有可复核证据。当前只有 Mac 环境，Windows 部署暂缓；因此先对已运行的本机 OrbStack 栈建立只读 HTTP 基准，同时明确它不是浏览器渲染时间。用户要求每次修改保留位置与决策过程。

## 决策过程

考虑用浏览器端到端计时，但它还涉及资源缓存、图表绘制和页面交互，首轮难以与服务查询耗时分开。先固定六个普通入口，每个首次 + 5 次重复读取，并以所有请求最大值对照 2 秒阈值；再由 D 在彩排中补浏览器体验。脚本只允许 loopback 目标、仅登录获取 Token，测量过程不创建研究记录。把首次读取称为“首次”，不宣称服务冷启动。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 安全校验本机 URL，测量六类入口并输出 JSON | `tools/benchmark_page_queries.py::require_loopback_url`、`measure`、`measure_views`、`main` | 可重复测量普通读取并按阈值返回退出码 |
| URL、计时、只读调用回归测试 | `backend/tests/test_page_query_benchmark.py::PageQueryBenchmarkTests` | 防止意外请求外部主机或变成写入式验收 |
| 保存 Mac 实测数值、样本规模和限制 | `docs/PAGE_QUERY_PERFORMANCE.md::2026-10-14 实测`、`不等同于完整页面性能验收` | 为课程汇报提供有限、可核对证据 |
| 更新 PRD 差距和文档入口 | `docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md::功能与验收矩阵`、`README.md::当前阶段边界` | 状态由未验改为部分验证 |
| 登记本次修改 | `docs/CHANGE_INDEX.md` 对应条目 | 统一追溯 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：133 项通过；黄金验算脚本通过；前端生产构建通过。
- `FACTORLAB_DEMO_VIEWER_PASSWORD` 设置为本机既有演示密码后运行 `.venv/bin/python tools/benchmark_page_queries.py`：Mac OrbStack 六入口均通过。最慢的任务列表最大值 0.0864 秒；此时列表含 26 个任务。详情见 [`../PAGE_QUERY_PERFORMANCE.md`](../PAGE_QUERY_PERFORMANCE.md)。
- Windows、浏览器完整渲染、并发和服务冷启动未测。

## 风险、回退与未决事项

这些数值不能外推到更大任务库或其他机器。若最终演示环境、数据规模变化，应重跑基准；若浏览器页面仍慢，要分别检查静态资源、渲染和 API，不应仅用本工具宣布 PRD 页面性能完全达标。
