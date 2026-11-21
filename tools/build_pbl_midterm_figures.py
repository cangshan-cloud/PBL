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


def task_failure_branches() -> None:
    img, d = canvas("M1 异步任务故障分支", "从创建 Run 到终态，区分入队、认领与执行阶段的故障")
    for xy, label, tint, border in [
        ((70, 275, 330, 405), "创建 Run\npending", "#EAF2F8", BLUE),
        ((450, 275, 710, 405), "发送队列\n消息", "#E7F5F4", TEAL),
        ((830, 275, 1090, 405), "条件认领\nrunning", "#EEF5E9", GREEN),
        ((1210, 275, 1470, 405), "执行研究\n写回产物", "#EAF2F8", BLUE),
        ((450, 485, 710, 590), "入队失败\n记录 failed", "#FDECEC", RED),
        ((830, 485, 1090, 590), "重复消息\n停止认领", "#FFF2E4", AMBER),
        ((1210, 485, 1470, 590), "异常或取消\n保存终态", "#FDECEC", RED),
    ]:
        box(d, xy, label, tint, border, 27)
    for x0, x1 in [(337, 443), (717, 823), (1097, 1203)]:
        arrow(d, (x0, 340), (x1, 340))
    for x in (580, 960, 1340):
        arrow(d, (x, 410), (x, 478), RED)
    note(d, "只有 pending 可标记入队失败；重复投递不产生第二次计算；终态保留日志与错误原因")
    img.save(ASSETS / "A_task_failure_branches.png", optimize=True)


def domain_model() -> None:
    img, d = canvas("M1 研究任务领域模型", "版本身份、参数快照、运行记录与产物之间的持久化关系")
    items = [
        ((85, 255, 375, 365), "User\n创建者", BLUE),
        ((85, 455, 375, 565), "DatasetVersion\n数据版本", GREEN),
        ((480, 350, 790, 470), "Experiment\n参数与代码版本", TEAL),
        ((900, 350, 1190, 470), "Run\n状态与结果", BLUE),
        ((1300, 230, 1640, 350), "RunLog\n事件日志", AMBER),
        ((1300, 470, 1640, 590), "Artifact\n报告与复现文件", GREEN),
    ]
    for xy, label, border in items:
        box(d, xy, label, "#F4F8FB", border, 28)
    arrow(d, (380, 310), (473, 375))
    arrow(d, (380, 510), (473, 445), GREEN)
    arrow(d, (797, 410), (893, 410))
    arrow(d, (1197, 390), (1293, 290), AMBER)
    arrow(d, (1197, 430), (1293, 530), GREEN)
    note(d, "Run 指向一次 Experiment；日志和产物按 Run ID 归档，数据修订不覆盖旧版本")
    img.save(ASSETS / "A_domain_model.png", optimize=True)


def role_matrix() -> None:
    img, d = canvas("M1 角色与资源权限矩阵", "以服务端 API 判定为准；研究员访问任务时还要核对创建者")
    left, top, row_h = 90, 220, 96
    widths = [250, 330, 330, 330, 330]
    headings = ["角色", "账号与数据发布", "创建与取消任务", "查看本人研究", "查看全部研究"]
    rows = [
        ["管理员", "允许", "允许", "允许", "允许"],
        ["研究员", "拒绝", "允许", "允许", "拒绝"],
        ["查看者", "拒绝", "拒绝", "只读", "只读"],
    ]
    for ri, row in enumerate([headings] + rows):
        x = left
        for ci, value in enumerate(row):
            y = top + ri * row_h
            d.rounded_rectangle((x, y, x + widths[ci] - 8, y + row_h - 8), radius=12,
                                fill="#DDEAF3" if ri == 0 else ("#F3F7FA" if ri % 2 else "#FFFFFF"),
                                outline="#BDCEDB", width=2)
            centered(d, (x, y, x + widths[ci] - 8, y + row_h - 8), value, 25, NAVY if ri == 0 else INK)
            x += widths[ci]
    note(d, "此图描述课程验收角色边界；具体端点以 API 权限依赖与 Run 归属检查复核")
    img.save(ASSETS / "A_role_matrix.png", optimize=True)


def release_gate() -> None:
    pipeline("A_release_gate.png", "组长交付放行流程", "每一项都要留下可定位的提交号、运行记录或人工确认",
             ["冻结代码\n与数据版本", "结构测试\n与回归", "隔离部署\n队列验收", "四人材料\n图件归档", "人工核对\n最终提交"],
             "材料生成、自动测试与人工产品验收分别记录；发现阻断问题返回对应阶段修正")


def dataset_lifecycle() -> None:
    img, d = canvas("M2 数据版本生命周期", "导入创建 draft；发布前检查质量与文件身份，旧版本不被新导入覆盖")
    box(d, (80, 280, 375, 420), "上传与解析\n创建新版本", "#EAF2F8", BLUE, 28)
    box(d, (545, 280, 840, 420), "draft\n待发布", "#FFF2E4", AMBER, 29)
    box(d, (1010, 280, 1305, 420), "发布门禁\n质量与文件核验", "#E7F5F4", TEAL, 27)
    box(d, (1470, 280, 1740, 420), "published\n可供研究", "#EEF5E9", GREEN, 28)
    box(d, (1010, 485, 1305, 585), "阻断错误\n保持不可选", "#FDECEC", RED, 26)
    for x0, x1 in [(382, 538), (847, 1003), (1312, 1463)]:
        arrow(d, (x0, 350), (x1, 350))
    arrow(d, (1158, 427), (1158, 478), RED)
    note(d, "修订文件应创建另一版本；已发布版本供 Run 固定引用，不能以新文件覆盖旧输入")
    img.save(ASSETS / "B_dataset_lifecycle.png", optimize=True)


def quality_decision() -> None:
    img, d = canvas("M2 数据发布质量决策树", "结构、业务质量与来源信息分别判断，失败原因必须能定位")
    box(d, (80, 290, 360, 430), "输入文件\n与来源", "#EAF2F8", BLUE, 28)
    box(d, (500, 290, 780, 430), "字段 日期 键\n是否合法", "#E7F5F4", TEAL, 27)
    box(d, (920, 290, 1200, 430), "业务质量\n有无阻断", "#E7F5F4", TEAL, 27)
    box(d, (1340, 290, 1620, 430), "发布版本\n供 Run 选择", "#EEF5E9", GREEN, 27)
    for x0, x1 in [(367, 493), (787, 913), (1207, 1333)]:
        arrow(d, (x0, 360), (x1, 360))
    box(d, (500, 500, 780, 590), "解析拒绝\n记录字段原因", "#FDECEC", RED, 24)
    box(d, (920, 500, 1200, 590), "发布拒绝\n保留质量报告", "#FFF2E4", AMBER, 24)
    arrow(d, (640, 435), (640, 493), RED)
    arrow(d, (1060, 435), (1060, 493), AMBER)
    note(d, "SHA-256 证明字节未变；来源授权仍需单独确认，不能由质量通过推断")
    img.save(ASSETS / "B_quality_decision.png", optimize=True)


def metric_dependencies() -> None:
    img, d = canvas("M3 研究指标依赖关系", "逐股观测先完成时间对齐，再形成多条可独立复核的指标链")
    box(d, (65, 320, 360, 455), "逐股因子值\n下一期收益", "#EAF2F8", BLUE, 26)
    box(d, (480, 320, 775, 455), "共同有效样本\n逐日截面", "#E7F5F4", TEAL, 27)
    for xy, label, color in [
        ((920, 215, 1215, 315), "IC / Rank IC", GREEN),
        ((920, 360, 1215, 460), "分组与多空收益", AMBER),
        ((920, 505, 1215, 605), "换手与成本", BLUE),
    ]:
        box(d, xy, label, "#F4F8FB", color, 26)
    box(d, (1370, 345, 1690, 470), "逐日序列汇总\n报告披露", "#EEF5E9", GREEN, 27)
    arrow(d, (367, 387), (473, 387))
    for y in (265, 410, 555):
        arrow(d, (782, 387), (913, y))
        arrow(d, (1222, y), (1363, 408))
    note(d, "有效样本、跳过原因和逐日原值随指标保存，汇总值不能靠图表截图反推")
    img.save(ASSETS / "C_metric_dependencies.png", optimize=True)


def valid_slice_decision() -> None:
    img, d = canvas("M3 逐日截面有效性判断", "样本不足与常数截面保留不可计算状态，不用零替代缺失指标")
    box(d, (80, 280, 340, 420), "交易日 t\n因子与标签", "#EAF2F8", BLUE, 28)
    box(d, (470, 280, 730, 420), "过滤缺失值\n形成共同样本", "#E7F5F4", TEAL, 26)
    box(d, (860, 280, 1120, 420), "样本数与方差\n满足口径", "#FFF2E4", AMBER, 26)
    box(d, (1250, 240, 1530, 350), "计算 IC\n分组与成本", "#EEF5E9", GREEN, 27)
    box(d, (1250, 470, 1530, 580), "记录跳过原因\n指标为缺失", "#FDECEC", RED, 26)
    arrow(d, (347, 350), (463, 350))
    arrow(d, (737, 350), (853, 350))
    arrow(d, (1127, 325), (1243, 295), GREEN)
    arrow(d, (1127, 395), (1243, 520), RED)
    note(d, "汇总只纳入有效日期；报告同时披露可用日期数与跳过原因")
    img.save(ASSETS / "C_valid_slice_decision.png", optimize=True)


def workspace_map() -> None:
    img, d = canvas("M4 研究工作台页面架构", "用户从配置进入 Run；回看、诊断、报告与导出均绑定同一身份")
    box(d, (80, 280, 380, 425), "配置页\n版本 因子 参数", "#EAF2F8", BLUE, 26)
    box(d, (520, 280, 820, 425), "任务中心\nRun ID 与状态", "#E7F5F4", TEAL, 26)
    for xy, label, color in [
        ((990, 205, 1280, 320), "结果诊断\n逐日原值", GREEN),
        ((990, 390, 1280, 505), "报告预览\n限制说明", AMBER),
        ((1430, 300, 1730, 445), "CSV JSON HTML\n复现包下载", BLUE),
    ]:
        box(d, xy, label, "#F4F8FB", color, 27)
    arrow(d, (387, 352), (513, 352))
    arrow(d, (827, 330), (983, 265))
    arrow(d, (827, 385), (983, 447))
    arrow(d, (1287, 265), (1423, 355))
    arrow(d, (1287, 447), (1423, 390))
    note(d, "切换 Run 时取消旧请求写回；文件名与正文继续披露完整 Run ID 和数据版本")
    img.save(ASSETS / "D_workspace_map.png", optimize=True)


def ui_state_machine() -> None:
    img, d = canvas("M4 任务页面状态机", "页面只展示服务端保存的 Run 状态；终态触发相应可用操作")
    for xy, label, color in [
        ((80, 270, 340, 390), "未选择\n提示配置", BLUE),
        ((470, 270, 730, 390), "pending\n显示等待", TEAL),
        ((860, 270, 1120, 390), "running\n进度与日志", TEAL),
        ((1250, 220, 1530, 330), "success\n查看报告", GREEN),
        ((1250, 390, 1530, 500), "failed\n显示原因", RED),
        ((1250, 540, 1530, 630), "cancelled\n保留记录", AMBER),
    ]:
        box(d, xy, label, "#F4F8FB", color, 26)
    arrow(d, (347, 330), (463, 330))
    arrow(d, (737, 330), (853, 330))
    arrow(d, (1127, 305), (1243, 275), GREEN)
    arrow(d, (1127, 350), (1243, 445), RED)
    arrow(d, (1127, 385), (1243, 585), AMBER)
    note(d, "用户切换任务时以当前完整 Run ID 更新页面；迟到响应不能把旧任务状态写到新任务")
    img.save(ASSETS / "D_ui_state_machine.png", optimize=True)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    architecture()
    state_machine()
    sequence()
    integration()
    permission_path()
    recovery_path()
    task_failure_branches()
    domain_model()
    role_matrix()
    release_gate()
    dataset_lifecycle()
    quality_decision()
    metric_dependencies()
    valid_slice_decision()
    workspace_map()
    ui_state_machine()
    pipeline("B_data_quality_gate.png", "M2 数据版本与质量门禁", "对应 CSV 导入、历史封存包校验和发布前检查", ["导入文件\n与来源说明", "字段 / 日期\n重复键检查", "SHA-256\n质量摘要", "无阻断错误\n通过门禁", "published\n研究选版"], "字节完整性、业务质量和来源授权分别记录；阻断错误存在时拒绝发布")
    pipeline("B_version_lineage.png", "M2 数据版本血缘", "每次导入产生独立版本，研究任务保存具体版本 ID", ["来源说明\n原始文件", "解析与质量\n检查结果", "版本 ID\nSHA-256", "published\n研究选择", "Run 参数\n报告披露"], "修订输入时创建新版本；旧 Run 继续引用其原版本与质量摘要")
    pipeline("C_signal_return_alignment.png", "M3 信号与下一期收益对齐", "逐交易日形成因子观测，保留缺失与不可计算状态", ["信号日 t\n已知行情", "因子值\n预处理", "下一期 t+1\n收益标签", "共同样本\n逐日 IC", "汇总 / 分组\n局限披露"], "常数截面与样本不足写为空值和原因；不能以零补出不存在的指标")
    pipeline("C_research_audit.png", "M3 指标独立核对链", "从保存的逐股观测与逐日序列复算汇总，不依赖页面图形", ["Run 参数\n版本身份", "逐股观测\n有效样本", "逐日 IC\n分组与成本", "汇总指标\n时间切分", "报告 / 复现包\n逐值核对"], "样本不足、常数截面和缺失标签保留状态；不把无法计算的日期计作零")
    pipeline("D_run_delivery_identity.png", "M4 同一 Run 的页面与交付", "工作台、任务中心、报告和下载读取保存的同一份研究结果", ["配置提交\n获得 Run ID", "状态与日志\n任务回看", "逐日诊断\n原值核对", "HTML 报告\n预览", "CSV / JSON\n复现包"], "完整 Run ID、数据版本和参数贯穿各出口；旧归档缺字段显示“未保存”")
    pipeline("D_request_identity.png", "M4 页面请求与 Run 身份", "用户切换任务时，迟到响应必须先通过当前身份检查", ["选择 Run A\n开始请求", "切换 Run B\n更新当前选择", "A 响应迟到\n身份不一致", "忽略 A 结果\n保留 B 状态", "下载请求\n只用当前 ID"], "曲线、原值、报告和下载均核对完整 Run ID；缺失字段只显示“未保存”")
    for path in sorted(ASSETS.glob("[ABCD]_*.png")):
        if path.name in {"A_platform_architecture.png", "A_run_state_machine.png", "A_async_sequence.png", "A_module_integration.png", "A_permission_path.png", "A_recovery_path.png", "A_task_failure_branches.png", "A_domain_model.png", "A_role_matrix.png", "A_release_gate.png", "B_data_quality_gate.png", "B_version_lineage.png", "B_dataset_lifecycle.png", "B_quality_decision.png", "C_signal_return_alignment.png", "C_research_audit.png", "C_metric_dependencies.png", "C_valid_slice_decision.png", "D_run_delivery_identity.png", "D_request_identity.png", "D_workspace_map.png", "D_ui_state_machine.png"}:
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
