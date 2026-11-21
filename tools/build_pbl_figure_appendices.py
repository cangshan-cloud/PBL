"""Build four standalone Word appendices for the PBL design diagrams."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "outputs/pbl-midterm-reports-2026-11-21/assets"
FINAL = ROOT / "outputs/pbl-figure-appendices-2026-11-22/final"


@dataclass(frozen=True)
class Figure:
    filename: str
    title: str
    kind: str
    use: str
    meaning: str
    basis: str
    check: str


MODULES = {
    "A": "平台基础与任务运行",
    "B": "数据集管理与质量控制",
    "C": "因子计算与研究检验",
    "D": "研究工作台与报告交付",
}


FIGURES: dict[str, tuple[Figure, ...]] = {
    "A": (
        Figure("A_platform_architecture.png", "五服务部署与数据流", "架构图", "PBL1 技术架构", "Web、API 和 Worker 承担不同职责；PostgreSQL 保存业务事实，Redis 传递队列消息。", "docker-compose.yml；backend/app/tasks.py；backend/app/models.py", "核对 Compose 服务名、数据库持久化和 Worker 连通性。"),
        Figure("A_run_state_machine.png", "Run 合法状态转换", "状态机", "PBL1 技术实现；PBL2 功能设计", "pending 经条件认领进入 running；success、failed 和 cancelled 为终态。", "backend/app/models.py::RunStatus；backend/app/services/runs.py::transition", "覆盖 pending 取消、running 取消请求、重复消息和终态不可重入。"),
        Figure("A_async_sequence.png", "异步研究任务时序", "时序图", "PBL2 功能设计", "API 保存 Run 并入队后返回完整 ID；Worker 随后认领，浏览器独立轮询。", "backend/app/main.py::create_task；backend/app/tasks.py::execute_research_run_task", "比较 HTTP 返回时间、Worker 日志、Run 最终状态和产物归属。"),
        Figure("A_module_integration.png", "四模块集成契约", "模块协作图", "PBL1 技术架构", "M2 发布版本，M1 保存 Run，M3 写研究结果，M4 按同一 Run 展示与交付。", "docs/TEAM_MODULE_DIVISION_2026-11-20.md；backend/app/models.py", "核对版本 ID、参数快照、Run ID 与报告身份在四模块中一致。"),
        Figure("A_permission_path.png", "后端授权检查路径", "流程图", "PBL1 技术架构", "身份和角色校验后，关联资源还需要回溯 Run 的创建者和资源归属。", "backend/app/main.py；backend/app/auth.py", "直接调用 API 验证越权拒绝；前端隐藏按钮不作为授权证据。"),
        Figure("A_recovery_path.png", "故障恢复核对顺序", "流程图", "PBL2 挑战与问题", "故障定位后核对迁移、数据库、旧 Run 和产物，再执行最小新任务。", "docker-compose.yml；backend/app/services/runs.py", "先检查旧数据可读，再检查新任务可执行；设计图不代表恢复演练已完成。"),
        Figure("A_task_failure_branches.png", "异步任务故障分支", "故障流程图", "PBL1 技术实现", "入队失败、重复消息与执行异常属于不同阶段，应分别保存原因和状态。", "backend/app/services/runs.py；backend/app/tasks.py", "入队失败只处理 pending；重复投递不得产生第二次计算。"),
        Figure("A_domain_model.png", "研究任务领域模型", "领域模型图", "PBL1 技术实现", "User、DatasetVersion、Experiment、Run、RunLog 和 Artifact 构成研究事实主线。", "backend/app/models.py", "从一条 Run 追溯创建者、数据版本、参数、日志及报告。"),
        Figure("A_role_matrix.png", "角色与资源权限矩阵", "权限矩阵", "PBL2 需求分析", "管理员可管理资源；研究员写入并读取本人研究；查看者只读研究结果。", "backend/app/main.py；backend/app/auth.py", "按三类角色分别验证写入、查看本人、查看全部和下载接口。"),
        Figure("A_release_gate.png", "组长交付放行流程", "交付流程图", "PBL2 下一步计划", "代码与数据冻结、回归、部署、四人材料和人工核对依次留证。", "docs/TEAM_MODULE_DIVISION_2026-11-20.md；docs/CHANGE_INDEX.md", "每一步记录提交号或实际输出；人工产品验收不得由材料生成代替。"),
    ),
    "B": (
        Figure("B_data_quality_gate.png", "数据版本质量门禁", "流程图", "PBL1 技术架构；PBL2 功能设计", "导入、字段与日期检查、文件摘要、阻断错误检查后才能发布。", "backend/app/services/datasets.py::import_csv；publish_dataset_version", "用缺列、重复键、非法日期和被篡改文件验证拒绝路径。"),
        Figure("B_version_lineage.png", "数据版本血缘", "血缘图", "PBL1 技术实现；PBL2 功能设计", "来源、质量报告、SHA-256 和版本 ID 共同确定一次研究的输入身份。", "backend/app/services/datasets.py；backend/app/models.py", "旧 Run 保留旧版本引用；修订输入应创建新版本。"),
        Figure("B_dataset_lifecycle.png", "数据版本生命周期", "状态流程图", "PBL1 技术实现", "导入产生 draft，质量门禁通过后进入 published；阻断错误使版本不可选。", "backend/app/services/datasets.py::import_csv；publish_dataset_version", "核对草稿与已发布版本在研究配置中的可选状态。"),
        Figure("B_quality_decision.png", "数据发布质量决策树", "决策图", "PBL2 功能设计", "结构错误在解析阶段拒绝；业务阻断在发布阶段拒绝并保留报告。", "backend/app/services/datasets.py::validate_csv；publish_dataset_version", "分别触发两类错误并记录可定位原因；来源授权单独确认。"),
    ),
    "C": (
        Figure("C_signal_return_alignment.png", "信号与下一期收益对齐", "时间流程图", "PBL1 技术架构；PBL2 功能设计", "信号日因子值对齐下一期收益标签，缺失和不可计算状态保留。", "backend/app/domain/research.py::evaluate；backend/app/domain/historical_research.py", "用小型黄金样例检查日期错位和未来信息使用。"),
        Figure("C_research_audit.png", "研究指标独立复算链", "审计流程图", "PBL1 技术实现；PBL2 功能设计", "从参数、逐股观测、逐日指标到汇总与报告逐层复算。", "backend/app/domain/research.py；tools/verify_historical_audit_exports.py", "复算有效样本数、逐日 IC 和汇总值，保留跳过原因。"),
        Figure("C_metric_dependencies.png", "研究指标依赖关系", "依赖图", "PBL1 技术实现", "共同有效样本分别用于 IC、分组、换手与成本，再形成逐日汇总。", "backend/app/domain/research.py::evaluate", "比较各指标使用的证券日期键和有效日期数。"),
        Figure("C_valid_slice_decision.png", "逐日截面有效性决策", "决策图", "PBL2 功能设计", "截面样本数或方差不足时保存缺失指标与跳过原因。", "backend/app/domain/research.py::evaluate", "构造常数截面和小样本截面，确认其不被当作零计入均值。"),
    ),
    "D": (
        Figure("D_run_delivery_identity.png", "同 Run 的页面与交付", "交付流程图", "PBL1 技术架构；PBL2 功能设计", "配置、任务回看、诊断、报告和多格式导出共享完整 Run ID。", "frontend/src/main.tsx；backend/app/services/reports.py", "比较页面标题、报告、CSV/JSON 与复现包的身份字段。"),
        Figure("D_request_identity.png", "页面请求身份守护", "请求流程图", "PBL1 技术实现；PBL2 功能设计", "切换 Run 后，旧请求的迟到响应不能覆盖当前结果。", "frontend/src/main.tsx", "快速切换 Run A/B 并延迟 A 响应，确认页面与下载保持 B 身份。"),
        Figure("D_workspace_map.png", "研究工作台页面架构", "页面架构图", "PBL1 技术架构", "配置页进入任务中心，再到诊断、报告预览和下载。", "frontend/src/main.tsx", "沿完整用户路径核对每处显示的 Run ID 与版本。"),
        Figure("D_ui_state_machine.png", "任务页面状态与可用操作", "页面状态图", "PBL2 功能设计", "未选择、等待、运行和三个终态对应不同提示与操作。", "frontend/src/main.tsx；backend/app/models.py::RunStatus", "核对成功入口、失败原因、取消记录和迟到响应处理。"),
    ),
}


def style_run(run, size: float, *, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = "PingFang SC"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "PingFang SC")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color or RGBColor(0, 0, 0)


def add_labelled_paragraph(doc: Document, label: str, value: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(5)
    para.paragraph_format.line_spacing = 1.12
    style_run(para.add_run(label), 10.5, bold=True)
    style_run(para.add_run(value), 10.5)


def add_page_number(paragraph) -> None:
    paragraph.add_run("第 ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    paragraph._p.append(field)
    paragraph.add_run(" 页")
    for run in paragraph.runs:
        style_run(run, 8.5)


def build_member(code: str) -> Path:
    figures = FIGURES[code]
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Inches(11.69), Inches(8.27)
    section.top_margin = Inches(0.64)
    section.bottom_margin = Inches(0.58)
    section.left_margin = Inches(0.76)
    section.right_margin = Inches(0.76)
    section.header_distance = Inches(0.28)
    section.footer_distance = Inches(0.28)

    normal = doc.styles["Normal"]
    normal.font.name = "PingFang SC"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "PingFang SC")
    normal.paragraph_format.space_after = Pt(4)
    title_style = doc.styles["Title"]
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    title_borders = title_style._element.get_or_add_pPr().find(qn("w:pBdr"))
    if title_borders is not None:
        title_borders.getparent().remove(title_borders)

    header = section.header.paragraphs[0]
    header.text = f"量化投资多因子研发平台  |  M{ord(code)-64} {MODULES[code]}"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:
        style_run(run, 8.5)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_page_number(footer)

    for index, item in enumerate(figures, 1):
        asset = ASSETS / item.filename
        if not asset.is_file():
            raise FileNotFoundError(asset)
        if index == 1:
            title = doc.add_paragraph(style="Title")
            title.paragraph_format.space_after = Pt(5)
            style_run(title.add_run(f"{MODULES[code]}设计图件附录"), 17, bold=True)
            intro = doc.add_paragraph()
            intro.paragraph_format.space_after = Pt(10)
            style_run(intro.add_run(f"成员 {code}｜共 {len(figures)} 张｜软件设计与验收口径图，可独立插入个人报告或答辩材料。"), 9.5)
        heading = doc.add_paragraph()
        if index > 1:
            heading.paragraph_format.page_break_before = True
        heading.paragraph_format.space_after = Pt(6)
        style_run(heading.add_run(f"图 {code}{index:02d}  {item.title}"), 14, bold=True)
        meta = doc.add_paragraph()
        meta.paragraph_format.space_after = Pt(8)
        style_run(meta.add_run(f"类型：{item.kind}    建议放置：{item.use}"), 9.5)
        figure_para = doc.add_paragraph()
        figure_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        figure_para.paragraph_format.space_after = Pt(10)
        figure_para.add_run().add_picture(str(asset), width=Inches(9.55 if index > 1 else 9.25))
        add_labelled_paragraph(doc, "图意：", item.meaning)
        add_labelled_paragraph(doc, "代码依据：", item.basis)
        add_labelled_paragraph(doc, "验收提示：", item.check)
        if index == 1:
            note = doc.add_paragraph()
            note.paragraph_format.space_before = Pt(5)
            style_run(note.add_run("图件性质：设计示意，不是运行截图、真实收益图或成员本人操作记录。"), 9)

    FINAL.mkdir(parents=True, exist_ok=True)
    output = FINAL / f"{code}_{MODULES[code]}_设计图件附录.docx"
    doc.core_properties.title = f"{MODULES[code]}设计图件附录"
    doc.core_properties.subject = "量化投资多因子研发平台 PBL 中期材料"
    doc.core_properties.author = f"成员 {code}【待填写姓名】"
    doc.save(output)
    return output


def main() -> None:
    for code in MODULES:
        output = build_member(code)
        print(f"{output.relative_to(ROOT)}\t{len(FIGURES[code])} figures\t{output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
