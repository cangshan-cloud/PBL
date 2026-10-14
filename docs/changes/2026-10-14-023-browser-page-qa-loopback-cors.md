# CHG-20261014-023：浏览器页面抽样与双 loopback 登录修正

- 日期：2026-10-14
- 类型：fix + browser QA + evidence
- 状态：verified on macOS OrbStack
- 关联提交：与本记录同次提交

## 背景与目标

上一轮普通查询验收仅覆盖宿主机 HTTP 与 JSON 解码，未包含真实浏览器。使用 Playwright CLI 在 Mac OrbStack 栈抽样时，`localhost:5173` 页面正常，但从同一宿主机的 `127.0.0.1:5173` 登录被默认 CORS 阻拦；浏览器首次访问还请求了缺失的 `favicon.ico`。两个地址都属于本机演示入口，因而应避免地址别名导致无提示登录失败。

## 决策过程

保留精确来源白名单，不使用 `*`。默认增加 `http://127.0.0.1:5173`，但用户显式设置 `CORS_ORIGINS` 时仍完全以其值为准。浏览器性能仅记录三次已登录刷新和每页一次导航，不把单次结果当成稳定百分位数；更完整的正式彩排仍由 D 完成。favicon 使用仓库原生 SVG，而非引入外部图片依赖。Playwright 技能引导使用隔离浏览器会话和频繁快照；生成的私有快照归档到忽略目录。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 默认 CORS 同时允许两个本机前端地址 | `backend/app/config.py::get_settings` | 127 地址打开前端时可完成 API 登录 |
| 默认设置与登录预检回归 | `backend/tests/test_config.py::ConfigTests`、`backend/tests/test_api_journey.py::ApiJourneyTests.test_default_loopback_frontends_can_preflight_login` | 防止再次遗漏别名；非白名单来源仍无允许头 |
| 声明并提供 SVG favicon | `frontend/index.html::<head>`、`frontend/public/favicon.svg` | 避免浏览器请求缺失图标产生 404 |
| 忽略私有浏览器 QA 产物 | `.gitignore::output/playwright/` | 快照不随 Git 分发 |
| 更新性能与部署边界 | `docs/PAGE_QUERY_PERFORMANCE.md::2026-10-14 浏览器抽样`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md::功能与验收矩阵`、`docs/ORBSTACK_DEPLOYMENT.md::启动`、`README.md` | 汇报口径和实际地址一致 |
| 登记本次修改 | `docs/CHANGE_INDEX.md` 对应条目 | 保留决策与证据 |

## 验证与结果

- `.venv/bin/python -m unittest discover -s backend/tests -q`：134 项通过；黄金验算和前端生产构建通过。
- 改动前的 `127.0.0.1:5173` Playwright 登录：浏览器报 CORS preflight 拒绝；`localhost:5173` 登录正常，五类只读页面导航时间分别为 29.5、31.5、150.7、100.9、31.7 ms。三次已登录刷新 FCP 为 88、36、44 ms；均为本机抽样，方法和限制见性能文档。
- 仅重建并替换 `fbl` 的 API/Web 后，`127.0.0.1:5173` 新浏览器会话登录成功、总览显示 2 个版本／26 个任务；`/favicon.svg` HTTP 200、登录 preflight HTTP 200、浏览器控制台 0 错误；db、redis、worker 保持运行，API/Worker/db/redis 健康，Web 运行中。
- Windows 浏览器与 Docker 离线部署未测。

## 风险、回退与未决事项

两个默认 CORS 来源仅供本机开发／演示，并不代表共享网络安全加固。显式 `CORS_ORIGINS` 会替换默认列表；自定义端口要自行填写。浏览器单次切页样本不足以估计高分位性能，且 iframe 出现不等于报告内部完全绘制。私有浏览器快照可能含演示账号输入，不应上传到仓库或公开分享。
