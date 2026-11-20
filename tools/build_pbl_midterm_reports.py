from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_pbl_assignment_docs as common  # noqa: E402


BASE = ROOT / "outputs" / "pbl-midterm-reports-2026-11-21"
TEMPLATES = BASE / "templates-converted"
ASSETS = BASE / "assets"
FINAL = BASE / "final"

TEMPLATE_FILES = {
    "pbl1": "学生需要提交的材料模板v6-PBL1-中期报告.docx",
    "pbl2": "学生需要提交的材料模板v6-PBL2-中期报告.docx",
}

COMMON_OVERVIEW = (
    "本项目建设量化投资多因子研发平台，面向少量研究人员提供版本化数据、因子计算、研究检验、"
    "异步任务、结果诊断和报告交付。平台部分解决权限、存储、任务调度和可复现等共性问题；"
    "产品部分把因子研究方法固化为可操作流程，形成因子检验报告与研究报告。"
)

COMMON_SCOPE = (
    "课程验收范围限定为国内股票市场的研究工具，不连接真实资金账户，不生成交易指令。"
    "首期采用模块化单体、PostgreSQL、Redis、Celery 和 Docker Compose，兼顾私域部署与课程周期，"
    "暂不拆分微服务，也不把 Windows 实机部署列为当前验收前置条件。"
)

COMMON_ARCHITECTURE = (
    "React 负责研究工作台、任务中心、实验对比和报告中心；FastAPI 提供认证、数据集、研究任务、"
    "比较和报告接口；Celery Worker 运行长耗时研究任务；PostgreSQL 保存用户、版本、Experiment、"
    "Run、日志和产物索引；Redis 仅承担队列与短期消息。所有结果以完整 Run ID 绑定数据版本、"
    "因子版本、参数、结构化结果和报告，避免页面与下载文件口径漂移。"
)

EXTRAS = {
    "A": {
        "implementation": [
            ("身份与权限", "实现 admin、researcher、viewer 三类角色；授权在 API 端执行，前端只承担交互提示。"),
            ("任务生命周期", "以 Experiment/Run 固化参数和版本，长任务交给 Celery；状态、进度、日志与失败原因持久化。"),
            ("部署与复现", "Docker Compose 编排 Web、API、Worker、PostgreSQL、Redis，并用迁移和健康检查保证可恢复。"),
        ],
        "progress": [
            ("权限与用户", "已完成", "登录、角色矩阵、资源归属和越权拒绝已有自动回归。"),
            ("异步 Run", "已完成", "提交、排队、执行、取消、失败、重试、日志和报告链路已接通。"),
            ("部署与审计", "已完成", "Mac OrbStack 五服务运行、数据库迁移、V2 复现包和健康检查已验证。"),
            ("收尾", "进行中", "最终冻结、备份恢复演练和队长人工产品验收待归档。"),
        ],
        "challenge": "难点是让长任务失败后仍可解释，同时避免重复 Worker 或非法状态跳转。解决方法是把状态转换集中到服务层，用条件更新抢占任务，并把日志、错误摘要、结果与报告全部绑定同一 Run。",
        "learning": "本阶段重点学习 FastAPI 依赖注入、SQLAlchemy 事务、Celery/Redis 任务模型、Alembic 迁移、Docker Compose 网络和基于角色的访问控制。",
        "next": "下一阶段冻结 API 和迁移版本，完成只读预检、备份恢复与队长人工验收；补齐部署说明和最终报告证据，不扩展独立微服务。",
        "design": "把认证、Run、Task、Artifact 四类业务单元转成模块化单体内部组件。创建任务快速返回 pending Run，Worker 独立执行并写回进度；成功后生成报告与复现包，失败则保留阶段和原因。",
        "code_path": "backend/app/tasks.py",
        "code": """settings = get_settings()
celery_app = Celery(
    \"factorlab\", broker=settings.redis_url, backend=settings.redis_url
)
celery_app.conf.update(task_track_started=True, task_serializer=\"json\")

@celery_app.task(name=\"factorlab.execute_research_run\")
def execute_research_run_task(run_id: str) -> str:
    with SessionLocal() as session:
        execute_research_run(session, run_id)
    return run_id""",
    },
    "B": {
        "implementation": [
            ("数据适配", "支持标准 CSV 与历史封存包，统一证券、交易日、OHLCV、换手率和估值字段。"),
            ("版本与质量", "保存数据版本、日期范围、证券数、行数、存储位置和 SHA-256；发布前执行质量门禁。"),
            ("真实样本", "完成 2024 年沪深300历史成员、行情与状态数据的私域封存、清单和逐文件哈希复验。"),
        ],
        "progress": [
            ("标准 CSV", "已完成", "字段、日期、重复键、非有限值、价格关系和预览已有校验。"),
            ("历史包", "已完成", "manifest、逐文件哈希、交易日、成员和逐股文件可只读核验。"),
            ("质量披露", "已完成", "覆盖、复权、成员范围、缺失和日历审计进入页面与报告。"),
            ("收尾", "进行中", "最终数据快照和来源/许可说明仍需队长按实际材料确认。"),
        ],
        "challenge": "难点是区分文件完整性、业务质量和数据授权。解决方法是分别保存 SHA-256、字段/业务质量报告和来源说明，任何阻断错误都拒绝发布，停牌缺失也不与采集失败混写。",
        "learning": "本阶段学习 A 股交易日历、前复权/后复权、历史指数成分、停牌与 ST 状态、CSV 安全解析、不可变数据包和数据血缘。",
        "next": "下一阶段固定最终数据版本，复核 manifest 和覆盖摘要，补齐来源与许可边界；保留真实私有数据不入仓库，只提交说明、哈希和验收证据。",
        "design": "数据产品流程为导入、解析、质量诊断、版本注册、发布和研究选择。研究任务只能绑定已发布版本；原始数据字节保存在受控目录，数据库只保存元数据、质量报告与路径。",
        "code_path": "backend/app/services/datasets.py::import_csv",
        "code": """parsed = validate_csv(content)
checksum = hashlib.sha256(content).hexdigest()
version_id = str(uuid4())
target = data_root / dataset_key / version / f\"{version_id}.csv\"
target.write_bytes(content)
dataset = DatasetVersion(
    id=version_id,
    start_date=parsed.start_date,
    end_date=parsed.end_date,
    row_count=parsed.row_count,
    symbol_count=parsed.symbol_count,
    checksum=checksum,
    quality_report={**parsed.report, **(quality_metadata or {})},
    status=\"draft\",
)""",
    },
    "C": {
        "implementation": [
            ("因子与预处理", "实现动量、反转、波动率、换手率、市值和市盈率，并支持去极值、标准化和等权合成。"),
            ("研究检验", "逐日计算 IC、Rank IC、分组收益、多空收益、换手、成本、净值和时间切分摘要。"),
            ("独立审计", "保存逐日序列、样本数与跳过状态，并用黄金样例和只读工具重新计算关键指标。"),
        ],
        "progress": [
            ("单因子", "已完成", "六类因子、窗口不足和空值规则已有单元测试。"),
            ("多因子", "已完成", "共同样本、成分 IC/Rank IC、逐日诊断与合成结果已保存。"),
            ("研究指标", "已完成", "IC、分组、多空、成本、覆盖和固定时间切分已完成复核。"),
            ("收尾", "进行中", "参数冻结、局限总结和队长最终研究解释仍需归档。"),
        ],
        "challenge": "难点是防止未来函数、样本错位、常数截面和缺失补零制造虚假结果。解决方法是严格用信号日对齐下一期收益，保留共同有效样本数，对不可计算日期写明状态而非写入零。",
        "learning": "本阶段学习截面因子研究、Pearson IC、Rank IC、分组检验、换手与交易成本、MAD 去极值、时间切分和幸存者偏差。",
        "next": "下一阶段冻结因子参数和费用口径，完成真实样本结果的最终审计与局限说明；结论只描述历史软件检验，不外推未来收益。",
        "design": "研究产品读取已发布数据版本，生成证券日期因子观测；预处理后用下一期收益计算 IC/Rank IC 与分组表现，保存逐日序列和汇总，再由页面、报告和导出共同读取。",
        "code_path": "backend/app/domain/research.py::evaluate",
        "code": """for item in observations:
    key = (item.trade_date, item.symbol)
    if key in seen:
        raise ValueError(f\"duplicate research observation: {key}\")
    seen.add(key)

processed = preprocess_observations(observations, winsorize=True)
for trade_date, daily in sorted(by_date.items()):
    factors = [item.factor for item in daily]
    returns = [item.forward_return for item in daily]
    ic = pearson(factors, returns)
    rank_ic = pearson(_rank(factors), _rank(returns))
    ic_series.append({\"date\": trade_date.isoformat(),
                      \"ic\": ic, \"rank_ic\": rank_ic})""",
    },
    "D": {
        "implementation": [
            ("研究工作台", "实现数据/因子/日期/预处理参数配置、提交前校验和配置变化后的旧结果隔离。"),
            ("任务与诊断", "展示状态、日志、逐日覆盖、IC/Rank IC、净值曲线、日期原值检查和旧 Run 回看。"),
            ("报告与导出", "提供 HTML 报告、CSV/JSON、复现包、实验对比与完整 Run 身份核对。"),
        ],
        "progress": [
            ("工作台", "已完成", "配置、异步提交、状态轮询、错误提示和结果归属已有回归。"),
            ("任务/报告", "已完成", "检索、归档、互相跳转、预览和下载链路已接通。"),
            ("可视化/导出", "已完成", "逐日图表、检查器、CSV/JSON/HTML 和离线核对已覆盖。"),
            ("收尾", "进行中", "页面文案微调、队长人工产品测试和最终用户手册待归档。"),
        ],
        "challenge": "难点是避免异步旧响应覆盖当前页面、不同 Run 结果串档以及空值在图中被补零。解决方法是以完整 Run ID 守护选择状态，取消重叠轮询，图表按已知日期并集绘制并保留断线。",
        "learning": "本阶段学习 React 状态管理、请求竞态、响应式布局、SVG 图表、Blob 下载、CSV 公式注入防护、HTML 转义和可访问性提示。",
        "next": "下一阶段按队长实际测试数据修正页面细节，完成用户手册、最终截图和交付文件核对；不新增与课程验收无关的复杂交互。",
        "design": "产品按配置、执行、回看、比较、解释和交付组织页面。前端不重新计算研究指标，只展示 Run 保存结果；报告、CSV、JSON 和复现包都带完整 Run ID 与版本信息。",
        "code_path": "frontend/src/main.tsx::downloadReport",
        "code": """async function downloadReport() {
  if (!selectedReport) return;
  setNotice(\"\");
  try {
    const filename = await downloadDisclosedReport(
      selectedReport.run_id, apiFetch, saveBlobAsFile
    );
    setNotice(`已发起 ${filename} 下载；请在浏览器下载列表确认文件。`);
  } catch (error) {
    setNotice(`披露版报告下载失败：${String(error)}`);
  }
}""",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fill_cover(doc: Document, code: str, module: dict) -> None:
    table = doc.tables[0]
    values = {
        (0, 1): f"【待填写：{module['owner']}】",
        (0, 3): "【待填写：学号】",
        (1, 1): "【待填写：班级】",
        (1, 3): "【待填写：任课教师】",
    }
    for (row, col), value in values.items():
        cell = table.cell(row, col)
        cell.text = value
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                common.set_run_font(run, size=10.5, color="000000")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    node = OxmlElement("w:tblHeader")
    node.set(qn("w:val"), "true")
    tr_pr.append(node)


def add_title(doc: Document, course: str, module: dict) -> None:
    title = doc.add_paragraph(f"量化投资多因子研发平台 {course.upper()} 中期报告", style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(3)
    for run in title.runs:
        common.set_run_font(run, size=16, bold=True, color="000000")
    meta = doc.add_paragraph(f"个人模块：{module['name']}    报告日期：2026-11-21")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_after = Pt(6)
    for run in meta.runs:
        common.set_run_font(run, size=9.5, color="555555")
    common.add_body(
        doc,
        "本报告按四人功能模块责任口径整理。共同章节反映小组统一方案，个人章节只覆盖本模块。"
        "实现与自动测试由队长统筹并由 Codex 辅助执行，不把代执行记录写成成员本人亲测。",
    )


def add_code_block(doc: Document, path: str, code: str) -> None:
    caption = doc.add_paragraph(f"代码位置：{path}")
    caption.paragraph_format.keep_with_next = True
    caption.paragraph_format.space_after = Pt(3)
    for run in caption.runs:
        common.set_run_font(run, size=9.5, bold=True, color="000000")
    table = doc.add_table(rows=1, cols=1)
    common.set_table_borders(table, color="B7C9D6", size=6)
    cell = table.cell(0, 0)
    common.shade_cell(cell, "F3F4F6")
    common.set_cell_margins(cell, top=100, start=140, bottom=100, end=140)
    cell.text = code
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        for run in paragraph.runs:
            common.set_run_font(run, size=8.5, color="000000", font="Courier New")


def add_common_status(doc: Document) -> None:
    common.add_table(
        doc,
        ["阶段", "当前结果", "验收边界"],
        [
            ("平台基础", "认证、数据库、异步任务、日志、报告与复现链路已形成", "Mac/OrbStack 为当前主要环境"),
            ("产品功能", "数据、因子、研究、诊断、对比和多格式交付已接通", "不连接真实资金账户"),
            ("真实样本", "2024 沪深300私域历史包已完成多轮只读复核", "来源授权与偏差单独披露"),
            ("项目收尾", "进入冻结、人工验收和最终文档阶段", "Windows 部署暂不作为当前前置条件"),
        ],
        [1.1, 3.0, 2.0],
        font_size=8.8,
    )


def build_pbl1(doc: Document, code: str, module: dict, diagram: Path) -> None:
    extra = EXTRAS[code]
    add_title(doc, "PBL1", module)
    common.add_heading(doc, "一 项目概述")
    common.add_body(doc, COMMON_OVERVIEW)
    common.add_body(doc, COMMON_SCOPE)
    common.add_heading(doc, "1 项目目标与范围", level=2)
    common.add_body(doc, "目标是让研究人员从可追溯的数据版本出发，按统一口径运行单因子或多因子研究，并获得可检查、可下载、可复现的结果。当前重点是准时完成课程验收闭环，而不是扩展实时交易或大规模协作。")
    add_common_status(doc)

    heading = common.add_heading(doc, "二 技术架构")
    heading.paragraph_format.page_break_before = True
    common.add_body(doc, COMMON_ARCHITECTURE)
    common.add_figure(doc, diagram, f"图1 {module['name']}在平台架构中的处理链")
    common.add_table(
        doc,
        ["层次", "主要技术", "职责"],
        [
            ("交互层", "React TypeScript", "配置、状态、诊断、对比和报告交付"),
            ("服务层", "FastAPI SQLAlchemy", "权限、版本、任务、结果和接口契约"),
            ("计算层", "Python Celery", "因子、检验、报告和长任务隔离"),
            ("基础设施", "PostgreSQL Redis Docker Compose", "持久化、队列、迁移和私域部署"),
        ],
        [1.0, 2.0, 3.1],
        font_size=8.8,
    )

    heading = common.add_heading(doc, "三 个人技术实现")
    heading.paragraph_format.page_break_before = True
    common.add_body(doc, f"本人的课程责任范围为{module['name']}。{module['architecture']}")
    common.add_table(doc, ["技术单元", "已实现内容"], extra["implementation"], [1.55, 4.6], font_size=9.0)
    common.add_heading(doc, "1 关键接口与约束", level=2)
    common.add_table(doc, ["接口或方法", "输入", "输出", "关键约束"], module["interfaces"], [1.45, 1.4, 1.4, 1.9], font_size=8.5)

    heading = common.add_heading(doc, "四 个人项目进展")
    heading.paragraph_format.page_break_before = True
    common.add_table(doc, ["工作项", "状态", "中期证据"], extra["progress"], [1.2, 0.9, 4.1], font_size=8.8)
    common.add_body(doc, "总体判断：核心闭环已经具备，当前工作从功能扩展转向冻结、复核和材料归档。这里的“已完成”指现有自动化或开发者代执行证据通过，不等同于成员本人已经完成最终人工产品验收。")
    common.add_heading(doc, "五 挑战与学习")
    common.add_body(doc, extra["challenge"], bold_lead="难点：")
    common.add_body(doc, extra["learning"], bold_lead="学习：")

    heading = common.add_heading(doc, "六 未来计划")
    heading.paragraph_format.page_break_before = True
    common.add_body(doc, extra["next"])
    common.add_heading(doc, "七 相关代码")
    common.add_body(doc, "以下代码只节选与本模块中期内容直接相关的核心片段，完整上下文和测试以仓库为准。")
    add_code_block(doc, extra["code_path"], extra["code"])
    common.add_heading(doc, "八 中期结论")
    common.add_body(doc, f"{module['name']}已经形成可说明、可测试、可追踪的中期成果。下一阶段坚持范围冻结和证据收口，优先保证课程验收材料与现有系统行为一致。")


def build_pbl2(doc: Document, code: str, module: dict, diagram: Path) -> None:
    extra = EXTRAS[code]
    add_title(doc, "PBL2", module)
    common.add_heading(doc, "一 项目概述")
    common.add_body(doc, COMMON_OVERVIEW)
    common.add_body(doc, "产品面向管理员、研究员和查看者。管理员维护账号和数据，研究员配置并运行研究，查看者只读核对授权结果。产品输出研究诊断和报告，不提供投资建议。")
    common.add_heading(doc, "1 产品范围与当前结论", level=2)
    common.add_body(doc, COMMON_SCOPE)
    add_common_status(doc)

    heading = common.add_heading(doc, "二 需求分析")
    heading.paragraph_format.page_break_before = True
    common.add_table(
        doc,
        ["类别", "小组统一需求", "可检查标准"],
        [
            ("功能", "数据版本、因子配置、异步研究、诊断、比较和报告", "主流程有明确输入、状态和结果出口"),
            ("准确性", "时间对齐、共同样本、空值和成本口径不静默改变", "逐日序列、样本数和跳过原因可核对"),
            ("安全", "角色权限、资源归属和私有数据边界", "越权拒绝，仓库不提交私有行情字节"),
            ("可复现", "Run 绑定数据、因子、参数、结果和报告", "复现包和多种出口具有同一完整 Run ID"),
            ("可用性", "少量研究人员可完成配置、回看和下载", "错误可理解，窄屏关键表格可局部滚动"),
        ],
        [0.9, 3.0, 3.0],
        font_size=8.7,
    )
    common.add_body(doc, "非功能边界包括：单机私域部署、API 快速返回、长任务异步执行、服务重启后元数据保留，以及所有研究限制在报告中披露。")

    heading = common.add_heading(doc, "三 个人功能设计")
    heading.paragraph_format.page_break_before = True
    common.add_body(doc, f"本人的产品责任范围为{module['name']}。{extra['design']}")
    common.add_figure(doc, diagram, f"图1 {module['name']}业务流程")
    common.add_heading(doc, "1 功能模块与验收", level=2)
    common.add_table(doc, ["类别", "需求", "验收标准"], module["requirements"], [0.9, 2.2, 3.1], font_size=8.7)

    heading = common.add_heading(doc, "2 算法 数据库与接口设计", level=2)
    heading.paragraph_format.page_break_before = True
    common.add_body(doc, module["tech"])
    common.add_heading(doc, "关键算法思路", level=2)
    common.add_pseudocode(doc, module["algorithm"])
    common.add_heading(doc, "关键接口", level=2)
    common.add_table(doc, ["接口或方法", "输入", "输出", "错误与约束"], module["interfaces"], [1.45, 1.35, 1.4, 2.0], font_size=8.4)
    common.add_heading(doc, "验收用例", level=2)
    common.add_table(doc, ["编号", "场景", "预期结果"], module["acceptance"], [0.9, 2.45, 2.85], font_size=8.7)

    heading = common.add_heading(doc, "四 挑战与问题")
    heading.paragraph_format.page_break_before = True
    common.add_body(doc, extra["challenge"])
    common.add_body(doc, f"当前限制：{module['innovation']} 该设计提高了可追踪性，但不能消除真实数据授权、样本偏差、回溯过拟合和最终人工验收风险。")
    common.add_heading(doc, "五 下一步计划")
    common.add_body(doc, extra["next"])
    common.add_heading(doc, "六 相关代码")
    common.add_body(doc, "以下片段用于说明本模块的软件组件转化；完整实现、异常分支和测试仍以仓库为准。")
    add_code_block(doc, extra["code_path"], extra["code"])


def build_document(code: str, module: dict, course: str) -> Path:
    template = TEMPLATES / TEMPLATE_FILES[course]
    output = FINAL / f"{code}_{module['short']}_{course.upper()}_中期报告.docx"
    diagram = ASSETS / f"{code}_{course}_midterm_diagram.png"
    common.draw_flow(module, "pbl1_2" if course == "pbl1" else "pbl2_1", diagram)
    shutil.copy2(template, output)
    doc = Document(output)
    common.normalize_existing_fonts(doc)
    common.style_answer_styles(doc)
    fill_cover(doc, code, module)
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.top_margin = Inches(0.62)
    section.bottom_margin = Inches(0.62)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)
    section.header_distance = Inches(0.25)
    section.footer_distance = Inches(0.25)
    if course == "pbl1":
        build_pbl1(doc, code, module, diagram)
    else:
        build_pbl2(doc, code, module, diagram)
    for table in doc.tables[2:]:
        if table.rows:
            set_repeat_table_header(table.rows[0])
    doc.core_properties.title = f"{module['short']} {course.upper()} 中期报告"
    doc.core_properties.subject = "量化投资多因子研发平台个人中期报告"
    doc.core_properties.author = f"{code}【待填写姓名】"
    doc.core_properties.comments = "基础信息使用占位符；实现与自动测试由队长统筹并由 Codex 辅助执行。"
    doc.save(output)
    return output


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    for path in FINAL.glob("*.docx"):
        path.unlink()
    outputs: list[Path] = []
    for code, module in common.MODULES.items():
        for course in ("pbl1", "pbl2"):
            outputs.append(build_document(code, module, course))
    print(f"built={len(outputs)}")
    for output in outputs:
        print(f"{output.relative_to(ROOT)}\t{output.stat().st_size}\t{sha256(output)}")


if __name__ == "__main__":
    main()
