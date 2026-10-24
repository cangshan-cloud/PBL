# CHG-20261022-008 Web 镜像锁文件安装与隔离启动

## 问题与决策

上一轮隔离 Web 构建在 `npm install` 阶段长时间无输出，中断后改用本机 Vite 完成页面实点。仓库已有 `frontend/package-lock.json`，但 Dockerfile 只复制 `package.json` 并重新解析依赖。决定复制锁文件并使用 `npm ci --no-audit --no-fund`，让镜像构建使用已锁定版本；这不保证任何网络环境都能下载依赖。实际执行者：Codex。

## 修改内容与位置

- `frontend/Dockerfile`：先复制 `package.json` 和 `package-lock.json`，再执行 `npm ci --no-audit --no-fund`。
- `docs/DEVELOPMENT_PLAN_2026-10-21.md`、`docs/PRD_ACCEPTANCE_MATRIX_2026-10-14.md`、`docs/CHANGE_INDEX.md` 及 A/B/C/D 四责任包：记录构建与隔离启动证据、未覆盖范围。

## 验证与边界

OrbStack 单独 `docker build` 成功，`npm ci` 安装 67 包约 15 秒；隔离 Compose 预检 PASS，五服务构建并启动，DB/Redis/API/Worker 健康，Web `127.0.0.1:15121/` 返回 HTTP 200（431 字节），API 健康响应 `status=ok`。本机前端 47 项测试及生产构建通过。精确隔离项目已 `down`，未使用 `-v`；专用卷及运行目录保留，主栈未动。

本轮仅验证容器化 Web 可构建、可启动并提供入口 HTML；没有重新做容器化浏览器登录、研究页互动或新任务提交，也没有证明离线构建、Windows 环境或队长本人验收。上一轮本机 Vite 浏览器互动证据仍见 [CHG-20261022-007](2026-10-22-007-price-basis-browser-qa.md)。
