# CHG-20261014-008：OrbStack 宿主机入口定向恢复与预检增强

- 日期：2026-10-14
- 类型：deployment recovery + tool correction
- 状态：verified，端口转发根因未定位
- 关联提交：与本记录同次提交

## 背景与目标

`CHG-20261014-007` 的只读预检发现原有 `fbl` Compose 容器虽健康，宿主机无法访问 API。继续开发的首要目标是恢复演示入口，并让预检自动覆盖 Web 页面，而非只检查 API 账号。

## 决策过程

先比对容器内 `/health`、`docker inspect` 端口映射、Mac `curl/lsof` 和 `orbctl doctor`：API、Web 两个宿主机端口均无监听，内部 API 正常，OrbStack 自检通过。没有证据支持修改业务代码、删除数据卷或全局重启 OrbStack。先只重启 `fbl-api-1`，8000 端口恢复；再只重启 `fbl-web-1`，5173 端口恢复。数据库、Redis、Worker 均保持运行。由于根因不明，这个恢复方法不写成普适修复。预检增加宿主机前端 HTML 读取，避免以后再次把健康容器误判为可演示。

## 修改内容与对应位置

| 内容 | 位置 | 影响 |
| --- | --- | --- |
| 从宿主机请求并识别 FactorLab 前端 HTML；支持 `--web-url` | `tools/check_demo_readiness.py::check_web_page`、`main` | 前端端口不可达时预检直接失败 |
| 前端正常、拒绝连接、错误页面回归测试 | `backend/tests/test_demo_readiness.py::test_web_entry_must_be_reachable_and_match_app` | 防止只查 API 的漏洞复发 |
| 定向恢复事实与限制 | `docs/ORBSTACK_DEPLOYMENT.md` 的“启动” | 区分容器健康与宿主机可达 |
| 更新预检范围和当前彩排状态 | `docs/DEMO_REHEARSAL.md` 的“会前只读预检” | 不再宣称原有入口仍不可用 |
| 登记记录 | `docs/CHANGE_INDEX.md` 的变更表 | 可追溯 |

## 验证与结果

- 重启前：`docker compose ps` 的 API、db、redis、worker 为 healthy；API 容器内部 `/health` 为 200；端口映射 `127.0.0.1:8000`；宿主机 API/Web 连接拒绝且无监听；`orbctl doctor` 通过。
- 分别执行 `docker compose restart api` 与 `docker compose restart web`；随后 Mac `curl` 的 API `/health` 和 Web 首页均通过，`lsof` 显示 OrbStack 在 `127.0.0.1:8000`、`:5173` 监听，原有五项服务正常。没有重建镜像、删除卷或重启数据库/Worker。
- 新版只读预检在原有 `fbl` 栈通过：Web 页面、三种角色、演示数据 2,400 行/20 股票、六因子和查看者任务/报告列表均 PASS。`make test`：115 项通过。

## 风险、回退与未决事项

端口监听丢失的根因未确定，可能复发；正式彩排仍应每次从宿主机运行预检。此次原有 API/Web 容器只被重启，持久化数据未删除；运行镜像仍是此前构建的版本，新审计 CSV 等后续代码不会因为重启自动进入容器。未在本次重复 Worker 新任务或真实浏览器彩排。
