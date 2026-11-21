"""Generate editable-source, submission-ready diagrams for PBL midterm reports."""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "outputs/pbl-midterm-reports-2026-11-21/assets"
FONT_PATH = "/System/Library/Fonts/PingFang.ttc"
W, H = 1800, 720
NAVY = "#173B5E"
BLUE = "#24547F"
TEAL = "#087E83"
GREEN = "#2D794B"
AMBER = "#AF671C"
RED = "#A33D3D"
INK = "#172230"
MUTED = "#5B6774"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, index=0)


def canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 18, W - 18, H - 18), radius=22, outline="#D8E3EC", width=3)
    d.text((65, 42), title, font=font(46), fill=NAVY)
    d.text((67, 110), subtitle, font=font(26), fill=MUTED)
    d.line((65, 160, W - 65, 160), fill="#C9D8E5", width=3)
    return img, d


def centered(d: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], label: str, size: int = 31, fill: str = INK) -> None:
    x0, y0, x1, y1 = xy
    lines = label.split("\n")
    f = font(size)
    line_h = size + 13
    start_y = (y0 + y1 - len(lines) * line_h) / 2 + 3
    for n, line in enumerate(lines):
        box = d.textbbox((0, 0), line, font=f)
        d.text(((x0 + x1 - (box[2] - box[0])) / 2, start_y + n * line_h), line, font=f, fill=fill)


def box(d: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], label: str, tint: str = "#EAF2F8", border: str = BLUE, size: int = 31) -> None:
    d.rounded_rectangle(xy, radius=21, fill=tint, outline=border, width=4)
    centered(d, xy, label, size)


def arrow(d: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = BLUE, width: int = 5) -> None:
    d.line((start, end), fill=color, width=width)
    x0, y0 = start
    x1, y1 = end
    if abs(x1 - x0) >= abs(y1 - y0):
        sign = 1 if x1 > x0 else -1
        points = [(x1, y1), (x1 - sign * 19, y1 - 11), (x1 - sign * 19, y1 + 11)]
    else:
        sign = 1 if y1 > y0 else -1
        points = [(x1, y1), (x1 - 11, y1 - sign * 19), (x1 + 11, y1 - sign * 19)]
    d.polygon(points, fill=color)


def note(d: ImageDraw.ImageDraw, text: str, y: int = 643) -> None:
    d.rounded_rectangle((65, y, W - 65, y + 48), radius=12, fill="#F1F5F8")
    centered(d, (75, y, W - 75, y + 48), text, size=24, fill="#394D60")


def pipeline(name: str, title: str, subtitle: str, labels: list[str], footer: str) -> None:
    img, d = canvas(title, subtitle)
    n = len(labels)
    gap = 55
    box_w = (W - 150 - gap * (n - 1)) // n
    y0, y1 = 280, 470
    for i, label in enumerate(labels):
        x0 = 75 + i * (box_w + gap)
        tint = ["#EAF2F8", "#E7F5F4", "#EEF5E9", "#FFF2E4", "#F4EAF3"][i % 5]
        border = [BLUE, TEAL, GREEN, AMBER, BLUE][i % 5]
        box(d, (x0, y0, x0 + box_w, y1), label, tint, border, 28)
        if i < n - 1:
            arrow(d, (x0 + box_w + 7, 375), (x0 + box_w + gap - 7, 375))
    note(d, footer)
    img.save(ASSETS / name, optimize=True)


def architecture() -> None:
    img, d = canvas("M1 平台部署与数据流", "与 docker-compose.yml 中 Web、API、Worker、PostgreSQL、Redis 五服务对应")
    box(d, (70, 250, 355, 385), "研究人员\n浏览器", "#EAF2F8")
    box(d, (445, 250, 730, 385), "Web\nReact", "#EAF2F8")
    box(d, (820, 250, 1105, 385), "API\nFastAPI", "#E7F5F4", TEAL)
    box(d, (1195, 250, 1480, 385), "Worker\nCelery", "#E7F5F4", TEAL)
    box(d, (820, 475, 1105, 595), "PostgreSQL\n业务持久化", "#EEF5E9", GREEN, 28)
    box(d, (1195, 475, 1480, 595), "Redis\n队列消息", "#FFF2E4", AMBER, 28)
    arrow(d, (360, 317), (438, 317))
    arrow(d, (735, 317), (813, 317))
    arrow(d, (1110, 317), (1188, 317))
    arrow(d, (960, 390), (960, 468), GREEN)
    arrow(d, (1337, 468), (1337, 390), AMBER)
    d.text((1510, 290), "任务执行\n结果查询", font=font(25), fill=MUTED, spacing=10)
    note(d, "API 与 Worker 共享数据库和受控数据目录；Redis 消息不是研究结果的保存位置")
    img.save(ASSETS / "A_platform_architecture.png", optimize=True)


def state_machine() -> None:
    img, d = canvas("M1 Run 状态机", "依据 backend/app/models.py::RunStatus 与 services/runs.py::transition")
    box(d, (140, 255, 425, 370), "pending\n待执行", "#EAF2F8")
    box(d, (740, 255, 1025, 370), "running\n执行中", "#E7F5F4", TEAL)
    box(d, (1350, 255, 1635, 370), "success\n成功", "#EEF5E9", GREEN)
    box(d, (420, 485, 705, 600), "failed\n失败", "#FDECEC", RED)
    box(d, (1100, 485, 1385, 600), "cancelled\n已取消", "#FFF2E4", AMBER)
    arrow(d, (430, 312), (733, 312))
    arrow(d, (1030, 312), (1343, 312), GREEN)
    arrow(d, (340, 375), (530, 478), RED)
    arrow(d, (875, 375), (700, 515), RED)
    arrow(d, (350, 375), (1095, 515), AMBER)
    arrow(d, (930, 375), (1115, 478), AMBER)
    d.text((490, 255), "Worker 条件认领", font=font(25), fill=MUTED)
    note(d, "终态不可继续转换；运行中取消先记录请求，再由 Worker 响应")
    img.save(ASSETS / "A_run_state_machine.png", optimize=True)


def sequence() -> None:
    img, d = canvas("M1 异步研究任务时序", "请求快速返回 Run ID，后台计算与浏览器轮询相互独立")
    xs = [210, 600, 990, 1380]
    labels = ["研究员 / Web", "FastAPI", "PostgreSQL / Redis", "Celery Worker"]
    for x, label in zip(xs, labels):
        box(d, (x - 155, 205, x + 155, 270), label, "#EAF2F8", BLUE, 25)
        d.line((x, 275, x, 575), fill="#B1C4D2", width=3)
    steps = [
        (210, 600, 314, "提交配置"),
        (600, 990, 365, "保存 Run / 入队"),
        (600, 210, 416, "立即返回 Run ID"),
        (990, 1380, 467, "按 Run ID 认领"),
        (1380, 990, 518, "写状态与结果"),
    ]
    for start_x, end_x, y, label in steps:
        arrow(d, (start_x + (18 if end_x > start_x else -18), y), (end_x - (18 if end_x > start_x else -18), y), TEAL)
        centered(d, (min(start_x, end_x), y - 34, max(start_x, end_x), y - 2), label, 23, INK)
    note(d, "失败、取消和重试均保留状态与日志；报告只读取成功 Run 的已保存产物")
    img.save(ASSETS / "A_async_sequence.png", optimize=True)


def integration() -> None:
    img, d = canvas("组长的四模块集成契约", "每一步以数据版本或完整 Run ID 对齐输入、结果和交付")
    labels = ["M2 数据集\n版本与质量", "M1 平台\n身份与任务", "M3 研究\n因子与检验", "M4 工作台\n诊断与报告"]
    for i, label in enumerate(labels):
        x = 65 + i * 440
        box(d, (x, 265, x + 340, 435), label, ["#EAF2F8", "#E7F5F4", "#EEF5E9", "#FFF2E4"][i], [BLUE, TEAL, GREEN, AMBER][i], 30)
        if i < 3:
            arrow(d, (x + 347, 350), (x + 430, 350))
    centered(d, (70, 485, 1730, 585), "发布版本 ID  →  Run 参数快照  →  结构化结果  →  同 Run 报告与导出", 29, NAVY)
    note(d, "M1 在所有环节提供授权、持久化、状态、日志与产物索引")
    img.save(ASSETS / "A_module_integration.png", optimize=True)


def permission_path() -> None:
    img, d = canvas("M1 授权检查路径", "入口校验身份，关联资源先解析 Run，再检查角色与资源归属")
    labels = ["请求与 Token\n识别调用者", "角色能力\n检查操作", "资源 ID\n解析关联 Run", "所有者 / 授权\n核对归属", "允许访问或\n返回拒绝"]
    n = len(labels)
    for i, label in enumerate(labels):
        x0 = 65 + i * 352
        box(d, (x0, 265, x0 + 280, 445), label,
            ["#EAF2F8", "#E7F5F4", "#EEF5E9", "#FFF2E4", "#FDECEC"][i],
            [BLUE, TEAL, GREEN, AMBER, RED][i], 27)
        if i < n - 1:
            arrow(d, (x0 + 287, 355), (x0 + 343, 355))
    note(d, "任务详情、报告与复现包下载均需执行授权；页面隐藏入口不替代 API 拒绝")
    img.save(ASSETS / "A_permission_path.png", optimize=True)


def recovery_path() -> None:
    img, d = canvas("M1 部署故障与恢复核对", "故障先保留现场证据，再定位服务依赖与持久化事实")
    labels = ["健康检查\n定位服务", "迁移与日志\n确定阶段", "数据库 / 产物\n核对身份", "隔离恢复\n复核旧 Run", "最小新任务\n验证链路"]
    for i, label in enumerate(labels):
        x0 = 65 + i * 352
        box(d, (x0, 265, x0 + 280, 445), label,
            ["#EAF2F8", "#E7F5F4", "#EEF5E9", "#FFF2E4", "#EAF2F8"][i],
            [BLUE, TEAL, GREEN, AMBER, BLUE][i], 27)
        if i < len(labels) - 1:
            arrow(d, (x0 + 287, 355), (x0 + 343, 355))
    note(d, "旧用户、版本、Run、日志与 Artifact 可读，再证明新任务可执行；Redis 不是恢复基准")
    img.save(ASSETS / "A_recovery_path.png", optimize=True)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    architecture()
    state_machine()
    sequence()
    integration()
    permission_path()
    recovery_path()
    pipeline("B_data_quality_gate.png", "M2 数据版本与质量门禁", "对应 CSV 导入、历史封存包校验和发布前检查", ["导入文件\n与来源说明", "字段 / 日期\n重复键检查", "SHA-256\n质量摘要", "无阻断错误\n通过门禁", "published\n研究选版"], "字节完整性、业务质量和来源授权分别记录；阻断错误存在时拒绝发布")
    pipeline("B_version_lineage.png", "M2 数据版本血缘", "每次导入产生独立版本，研究任务保存具体版本 ID", ["来源说明\n原始文件", "解析与质量\n检查结果", "版本 ID\nSHA-256", "published\n研究选择", "Run 参数\n报告披露"], "修订输入时创建新版本；旧 Run 继续引用其原版本与质量摘要")
    pipeline("C_signal_return_alignment.png", "M3 信号与下一期收益对齐", "逐交易日形成因子观测，保留缺失与不可计算状态", ["信号日 t\n已知行情", "因子值\n预处理", "下一期 t+1\n收益标签", "共同样本\n逐日 IC", "汇总 / 分组\n局限披露"], "常数截面与样本不足写为空值和原因；不能以零补出不存在的指标")
    pipeline("C_research_audit.png", "M3 指标独立核对链", "从保存的逐股观测与逐日序列复算汇总，不依赖页面图形", ["Run 参数\n版本身份", "逐股观测\n有效样本", "逐日 IC\n分组与成本", "汇总指标\n时间切分", "报告 / 复现包\n逐值核对"], "样本不足、常数截面和缺失标签保留状态；不把无法计算的日期计作零")
    pipeline("D_run_delivery_identity.png", "M4 同一 Run 的页面与交付", "工作台、任务中心、报告和下载读取保存的同一份研究结果", ["配置提交\n获得 Run ID", "状态与日志\n任务回看", "逐日诊断\n原值核对", "HTML 报告\n预览", "CSV / JSON\n复现包"], "完整 Run ID、数据版本和参数贯穿各出口；旧归档缺字段显示“未保存”")
    pipeline("D_request_identity.png", "M4 页面请求与 Run 身份", "用户切换任务时，迟到响应必须先通过当前身份检查", ["选择 Run A\n开始请求", "切换 Run B\n更新当前选择", "A 响应迟到\n身份不一致", "忽略 A 结果\n保留 B 状态", "下载请求\n只用当前 ID"], "曲线、原值、报告和下载均核对完整 Run ID；缺失字段只显示“未保存”")
    for path in sorted(ASSETS.glob("[ABCD]_*.png")):
        if path.name in {"A_platform_architecture.png", "A_run_state_machine.png", "A_async_sequence.png", "A_module_integration.png", "A_permission_path.png", "A_recovery_path.png", "B_data_quality_gate.png", "B_version_lineage.png", "C_signal_return_alignment.png", "C_research_audit.png", "D_run_delivery_identity.png", "D_request_identity.png"}:
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
