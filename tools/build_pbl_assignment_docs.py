from __future__ import annotations

import hashlib
import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "pbl-assignments-2026-11-20"
TEMPLATES = BASE / "templates-converted"
ASSETS = BASE / "assets"
FINAL = BASE / "final"
FONT_NAME = "PingFang SC"
DIAGRAM_FONT_PATH = "/System/Library/Fonts/PingFang.ttc"


TEMPLATE_FILES = {
    "pbl1_1": "学生需要提交的材料模板v6-PBL1-作业1.docx",
    "pbl1_2": "学生需要提交的材料模板v6-PBL1-作业2.docx",
    "pbl2_1": "学生需要提交的材料模板v6-PBL2-作业1.docx",
    "pbl2_2": "学生需要提交的材料模板v6-PBL2-作业2.docx",
}


MODULES = {
    "A": {
        "owner": "队长姓名",
        "name": "M1 平台基础与任务运行模块",
        "short": "平台基础与任务运行",
        "units": [
            ("身份与访问控制", "接收账号凭据并生成身份上下文；后端按 admin、researcher、viewer 校验资源权限。", "凭据与角色 → Token、用户信息和访问判定", "授权必须在 API 端执行，前端隐藏按钮不能替代权限校验。"),
            ("Run 与异步任务运行", "把研究参数固化为 Experiment/Run，经 Redis 交给 Celery Worker，状态和日志写入 PostgreSQL。", "研究参数和版本 → 状态、进度、日志、结果与报告索引", "长计算不阻塞 API；只允许规定的状态迁移，失败原因可追踪。"),
        ],
        "scenario": "研究员登录后创建研究任务，API 持久化 pending Run 并入队；Worker 将其转为 running，完成后进入 success，异常或取消分别进入 failed/cancelled。",
        "interfaces": [
            ("POST /api/v1/auth/login", "用户名、密码", "Token 与用户角色", "无效凭据拒绝，不泄露密码哈希"),
            ("POST /api/v1/research/tasks", "数据版本、因子版本、参数", "Experiment 与 pending Run", "研究员可创建，查看者禁止写入"),
            ("GET /api/v1/research/tasks/{id}", "Run ID", "状态、进度、结果摘要", "只返回当前用户获授权资源"),
        ],
        "problem": "少量研究人员也需要隔离权限、可靠执行长任务和保留可复现记录。若 API 同步计算，浏览器连接中断会丢失过程；若状态可任意改写，报告与 Run 身份会失去可信度。",
        "architecture": "采用模块化单体 FastAPI 与独立 Celery Worker。Web 只访问 API；PostgreSQL保存用户、版本、Experiment、Run、日志和产物索引；Redis 只承担队列与短期消息。Docker Compose 统一编排五个服务。",
        "algorithm": [
            "assert current.status in {PENDING, RUNNING}",
            "if current.status == PENDING: compare_and_set(PENDING, RUNNING)",
            "execute_research(run_id); persist_result_and_report(run_id)",
            "transition(RUNNING, SUCCESS); progress = 100",
            "on error: transition(RUNNING, FAILED, error_summary)",
        ],
        "innovation": "把状态转换、产物身份和复现信息绑定到同一个 Run，既保留模块化单体的低部署成本，又获得异步隔离、失败可追踪和结果可审计能力。",
        "business": "面向少量研究人员提供登录、任务提交、进度日志、失败处理和结果归档。管理员维护账号和数据；研究员创建任务；查看者只读查看授权结果。",
        "requirements": [
            ("功能", "登录与角色授权", "未登录拒绝；三类角色权限符合矩阵"),
            ("功能", "异步 Run 生命周期", "状态、进度、日志和失败原因可查询"),
            ("性能", "API 快速返回", "创建任务后立即返回 Run，不等待研究计算"),
            ("可靠性", "持久化与恢复", "服务重启后 Run、日志和报告索引仍存在"),
        ],
        "acceptance": [
            ("A-01", "研究员提交合法参数", "生成 pending Run，Worker 完成后为 success"),
            ("A-02", "viewer 尝试创建任务", "API 拒绝写操作且不创建 Run"),
            ("A-03", "Worker 计算异常", "Run 为 failed，日志包含可理解的失败阶段"),
        ],
        "components": ["Auth 组件", "Experiment/Run 组件", "Celery Task 组件", "Artifact/Report 索引组件"],
        "tech": "FastAPI、SQLAlchemy、PostgreSQL、Redis、Celery 和 Docker Compose。关键写入使用事务；状态抢占使用条件更新，防止重复 Worker 同时执行。",
        "tests": "单元测试覆盖权限与非法状态转换；集成测试覆盖 API→Redis→Worker→数据库→报告；部署检查覆盖健康接口、迁移版本、Worker ping 和持久化查询。",
        "flows": {
            "pbl1_1": ["研究员登录", "API 鉴权", "创建 pending Run", "Worker 执行", "success 或 failed"],
            "pbl1_2": ["React Web", "FastAPI 与权限", "Run 服务", "Celery Worker", "PostgreSQL 与 Redis"],
            "pbl2_1": ["配置研究参数", "提交异步任务", "查看进度日志", "查看结果", "下载报告"],
            "pbl2_2": ["Auth 组件", "Run 组件", "Task 组件", "Artifact 组件", "部署与健康检查"],
        },
    },
    "B": {
        "owner": "成员B姓名",
        "name": "M2 数据集管理与质量控制模块",
        "short": "数据集管理与质量控制",
        "units": [
            ("数据版本注册", "解析 CSV 或历史封存包，记录市场、频率、日期、证券数、行数、存储位置与 SHA-256。", "原始文件与元数据 → 不可变 DatasetVersion", "同一 dataset_key 与 version 唯一；研究任务只能绑定已发布版本。"),
            ("质量门禁", "校验表头、列数、日期、重复键、非有限值、价格关系、复权标记和覆盖摘要。", "候选数据 → 质量报告、异常明细与发布判定", "失败必须明确原因；停牌缺失与采集缺失不能混为一类。"),
        ],
        "scenario": "管理员导入 A 股日频数据，系统先解析字段和日期，再执行质量规则、计算摘要与校验和；通过后发布不可变版本，失败则保留问题说明而不进入研究。",
        "interfaces": [
            ("POST /api/v1/datasets/import", "CSV 与数据集元信息", "DatasetVersion 与质量报告", "仅管理员可写，重复版本拒绝"),
            ("POST /api/v1/datasets/{id}/publish", "DatasetVersion ID", "published 状态", "质量门禁未通过不得发布"),
            ("GET /api/v1/datasets/{id}/preview", "DatasetVersion ID", "字段、样例和摘要", "只读取获授权数据，私有原始包不公开"),
        ],
        "problem": "因子结论高度依赖数据口径。覆盖缺口、重复证券日期、错误复权或文件被替换，都会造成无法解释的结果差异；仅保存文件名不能支持复现。",
        "architecture": "数据集页面调用 Dataset Service；服务将元数据和质量报告写入 PostgreSQL，把数据文件保存到受控目录，并以 SHA-256 绑定内容。历史沪深 300 包还需校验清单、交易日、成员表和逐股文件。",
        "algorithm": [
            "parse_header_and_rows(file); reject duplicate(symbol, trade_date)",
            "check required fields, finite numbers and price constraints",
            "summarize dates, symbols, rows, adjustment basis and coverage",
            "checksum = sha256(file_bytes); persist DatasetVersion(status=draft)",
            "publish only when blocking_errors is empty",
        ],
        "innovation": "将文件哈希、字段模式、业务摘要和质量报告同时绑定到数据版本，使“文件没变”和“业务含义满足约束”成为两个可分别验证的层次。",
        "business": "为管理员和研究员提供可选择的数据版本，而不是临时读取未知 CSV。研究员在任务前即可看到市场、频率、日期范围、证券数、行数、复权口径和已知限制。",
        "requirements": [
            ("功能", "导入与版本化", "生成唯一版本、摘要和 SHA-256"),
            ("功能", "质量诊断", "重复键、缺字段、异常数值和覆盖不足可定位"),
            ("准确性", "业务口径披露", "复权、日期、成员范围和缺失原因可追踪"),
            ("安全", "私有数据保护", "仓库只保存说明和校验信息，不公开私有行情字节"),
        ],
        "acceptance": [
            ("B-01", "导入合法演示 CSV", "版本、摘要、质量报告和预览一致"),
            ("B-02", "导入重复证券日期", "发布被拒并指出重复键"),
            ("B-03", "修改封存包任一文件", "SHA-256 校验失败，研究加载停止"),
        ],
        "components": ["CSV/封存包适配器", "DatasetVersion 服务", "Quality Gate", "Preview 与发布接口"],
        "tech": "FastAPI 接收导入请求，Pandas/标准库完成解析，SQLAlchemy 保存版本与质量报告，受控目录保存数据字节。历史包以 manifest 和逐文件哈希实现只读封存。",
        "tests": "构造合法、缺列、重复键、非有限值、错误复权标记和篡改哈希样本；核对 API 状态码、质量报告、发布状态以及研究任务实际绑定的版本 ID。",
        "flows": {
            "pbl1_1": ["上传 CSV 或封存包", "解析字段日期", "执行质量规则", "计算摘要与哈希", "发布或拒绝"],
            "pbl1_2": ["数据集页面", "Dataset Service", "Quality Gate", "版本元数据", "只读数据包"],
            "pbl2_1": ["管理员导入", "查看质量诊断", "修复或确认限制", "发布版本", "研究员选择版本"],
            "pbl2_2": ["Adapter 组件", "Schema 校验", "Quality 组件", "Version 组件", "Preview/Publish API"],
        },
    },
    "C": {
        "owner": "成员C姓名",
        "name": "M3 因子计算与研究检验模块",
        "short": "因子计算与研究检验",
        "units": [
            ("因子计算与预处理", "按数据版本计算动量、反转、波动率、换手率、市值和市盈率，并执行去极值、标准化和等权合成。", "日频行情与参数 → 证券日期因子观测", "信号形成日与下一期收益严格错开；空值和常数截面不补零。"),
            ("研究检验", "在逐日截面计算 IC、Rank IC、分组收益、多空收益、换手率、成本和时间切分摘要。", "因子观测与未来收益 → 指标序列、摘要和诊断", "共同样本数、跳过日期和费用口径必须随结果保存。"),
        ],
        "scenario": "研究任务读取已发布数据版本，按规则计算因子并预处理；检验引擎用下一期收益进行相关性和分组检验，保存逐日序列、汇总指标及风险披露。",
        "interfaces": [
            ("Factor.compute", "价格、成交量、估值字段与窗口", "逐证券因子值", "窗口不足返回空值，不使用未来数据"),
            ("Research.evaluate", "同日因子截面与下一期收益", "IC、Rank IC、分组与多空序列", "至少满足有效样本和非恒定截面"),
            ("Composite.evaluate", "多个成分因子及共同键", "合成结果与成分 IC 诊断", "共同样本上比较，缺失不填零"),
        ],
        "problem": "因子研究容易因未来函数、样本错位、空值补零或成本遗漏产生虚假结论。只展示一个汇总值，无法判断稳定性、覆盖率和时间切分表现。",
        "architecture": "研究服务调用因子函数、预处理器、单因子/多因子检验器和结果审计器。计算层只产生结构化结果，报告和前端读取同一份保存数据，不在展示层重新计算。",
        "algorithm": [
            "for date in signal_dates: align factor(date) with return(next_date)",
            "drop non-finite pairs; if sample too small or factor constant: mark skipped",
            "ic = pearson(factor, future_return); rank_ic = spearman(...) ",
            "quantile_sort factor; compute group and long-short return minus turnover cost",
            "persist daily series, sample counts, aggregate metrics and split diagnostics",
        ],
        "innovation": "除组合指标外，保存各成分在同一共同样本上的逐日 IC/Rank IC 和样本数，使研究员能区分组合表现、成分贡献和数据覆盖差异。",
        "business": "研究员选择数据版本、因子和参数后获得统一检验结果。产品强调研究诊断与可复现，不生成交易指令，也不把历史相关性表述为未来收益保证。",
        "requirements": [
            ("功能", "六因子与多因子合成", "参数和版本可追踪，结果可重复"),
            ("准确性", "信号收益时间对齐", "因子日 t 只检验下一期收益，不使用未来字段"),
            ("诊断", "逐日序列与覆盖", "IC、样本数、跳过状态和日期均保存"),
            ("风险", "成本与偏差披露", "换手成本、固定股票池和数据限制写入结果"),
        ],
        "acceptance": [
            ("C-01", "固定黄金样例", "IC、Rank IC、分组和成本结果与独立期望一致"),
            ("C-02", "常数因子截面", "标记跳过，不伪造零 IC"),
            ("C-03", "多因子共同样本", "成分逐日样本数与共同有效键严格一致"),
        ],
        "components": ["Factor 计算组件", "预处理组件", "Research 评估组件", "Composite 与独立审计组件"],
        "tech": "Python 数值计算模块保持纯函数边界；服务层负责版本、任务和持久化。黄金样例与独立核对工具从保存观测重新计算，避免只用同一实现自证。",
        "tests": "覆盖窗口不足、缺失值、常数截面、正负相关、分组边界、换手成本、时间切分和共同样本；真实样本结论仅作为软件链路证据，不作投资建议。",
        "flows": {
            "pbl1_1": ["读取版本化数据", "计算因子", "去极值与标准化", "IC/分组检验", "保存指标与诊断"],
            "pbl1_2": ["DatasetVersion", "Factor Engine", "Preprocessor", "Research Engine", "Result Audit"],
            "pbl2_1": ["选择因子参数", "生成异步任务", "计算逐日观测", "检验与切分", "查看结论限制"],
            "pbl2_2": ["Factor 组件", "Composite 组件", "IC 组件", "Group/Cost 组件", "Audit 组件"],
        },
    },
    "D": {
        "owner": "成员D姓名",
        "name": "M4 研究工作台与报告交付模块",
        "short": "研究工作台与报告交付",
        "units": [
            ("研究工作台与任务回看", "收集数据版本、因子、日期和预处理参数，创建任务并展示状态、日志、图表和逐日值。", "用户配置与 Run API → 可操作的研究流程", "参数校验在前后端同时执行；页面只展示已保存结果。"),
            ("报告与多格式交付", "按 Run 生成 HTML 报告并提供 CSV、JSON、HTML 下载、实验对比和交付校验。", "Run 结果与复现信息 → 报告、导出文件和身份摘要", "所有出口绑定同一完整 Run ID，旧结果缺字段时明确提示。"),
        ],
        "scenario": "研究员在工作台配置并提交任务，在任务中心查看进度和日志；成功后核对图表、日期和样本数，进入报告中心预览并下载同一 Run 的 CSV、JSON 和 HTML。",
        "interfaces": [
            ("研究配置表单", "数据、因子、日期与参数", "研究任务请求", "必填与范围校验，提交后锁定 Run 身份"),
            ("GET /api/v1/research/tasks/{id}", "Run ID", "状态、结果和诊断", "轮询不重叠；离开页面停止请求"),
            ("GET /api/v1/reports/{run_id}/delivery", "Run ID", "报告交付摘要", "报告、复现包和任务身份必须一致"),
        ],
        "problem": "研究结果分散在任务、图表和下载文件时，用户难以确认是否属于同一次运行。自动刷新若重叠会增加请求；缺失日期若被连线或补零，会误导研究判断。",
        "architecture": "React 统一承载研究工作台、任务中心、实验对比和报告中心；FastAPI 提供任务、日志、比较、报告和下载接口；报告服务从 Run 保存结果生成 HTML，前端导出也使用同一结果对象。",
        "algorithm": [
            "load authorized Run by full run_id",
            "render charts from saved daily series; keep null as gap",
            "build CSV/JSON/HTML metadata with the same run_id and versions",
            "escape spreadsheet-formula prefixes and HTML text",
            "verify downloaded identity and checksum before acceptance",
        ],
        "innovation": "在图表旁提供逐日原值和样本数检查器，并把任务、报告、复现包和导出文件用完整 Run ID 串联，降低“看起来一致但实际来自不同运行”的风险。",
        "business": "产品把研究方法转成可操作流程：配置、执行、回看、比较、解释和交付。少量研究人员优先需要清晰、稳定和可核对，而不是复杂协同或实时交易界面。",
        "requirements": [
            ("功能", "研究配置与任务回看", "参数可理解；状态、日志和结果可追踪"),
            ("功能", "图表、表格与日期检查", "空值断线，不补零；原值与样本数可核对"),
            ("交付", "报告和多格式下载", "HTML、CSV、JSON 均绑定同一 Run"),
            ("可用性", "刷新与窄屏布局", "轮询不重叠，关键表格可横向滚动"),
        ],
        "acceptance": [
            ("D-01", "研究员提交并完成任务", "工作台、任务中心和报告显示同一 Run"),
            ("D-02", "逐日序列存在缺值", "图表断线，检查器显示未保存而非 0"),
            ("D-03", "下载 CSV/JSON/HTML", "Run ID、版本、日期和摘要可离线核对"),
        ],
        "components": ["ResearchConfig 组件", "TaskCenter 组件", "Chart/Table 组件", "Report/Export 组件"],
        "tech": "React 与 TypeScript 负责表单和可视化，FastAPI 报告服务生成 HTML。公共导出函数处理 CSV 转义、Blob 下载、完整 Run ID 和浏览器兼容。",
        "tests": "前端单测覆盖参数映射、空值断线、日期并集、CSV 转义和旧结果提示；浏览器验收覆盖登录、提交、回看、比较、预览、下载及只读权限。",
        "flows": {
            "pbl1_1": ["工作台配置", "提交 Run", "任务中心轮询", "图表逐日核对", "报告与下载"],
            "pbl1_2": ["React 页面", "Task API", "Saved Result", "Report Service", "CSV/JSON/HTML"],
            "pbl2_1": ["选择数据因子", "提交任务", "查看日志结果", "实验对比", "交付研究报告"],
            "pbl2_2": ["Config 组件", "Task 组件", "Chart/Table", "Comparison", "Report/Export"],
        },
    },
}


ASSIGNMENTS = {
    "pbl1_1": {
        "course": "PBL1",
        "label": "作业1",
        "title": "{short}核心单元识别与交互建模",
        "submission": "提交物：1–2页设计说明 + 相关模型图（流程图、时序图、状态机等）。",
    },
    "pbl1_2": {
        "course": "PBL1",
        "label": "作业2",
        "title": "{short}关键组件架构与实现方案",
        "submission": "提交物：2页设计文档 + 架构图 + 关键算法伪代码或数据模型。",
    },
    "pbl2_1": {
        "course": "PBL2",
        "label": "作业1",
        "title": "{short}业务逻辑与产品方案设计",
        "submission": "提交物：2–3页产品方案 + 业务流程图 + 功能/非功能需求表 + 验收用例。",
    },
    "pbl2_2": {
        "course": "PBL2",
        "label": "作业2",
        "title": "{short}业务组件化与技术实现",
        "submission": "提交物：2–3页组件实现说明 + 组件架构图 + 关键接口契约 + 实现与测试要点。",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def set_run_font(run, size: float | None = None, bold: bool | None = None, color: str | None = None, font: str = FONT_NAME):
    run.font.name = font
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)


def all_paragraphs(doc: Document):
    for paragraph in doc.paragraphs:
        yield paragraph
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    yield paragraph


def normalize_existing_fonts(doc: Document):
    for paragraph in all_paragraphs(doc):
        for run in paragraph.runs:
            set_run_font(run)


def replace_paragraph(paragraph, text: str, prefix: str | None = None):
    paragraph.clear()
    if prefix and text.startswith(prefix):
        first = paragraph.add_run(prefix)
        set_run_font(first, bold=True, color="000000")
        rest = paragraph.add_run(text[len(prefix):])
        set_run_font(rest, color="000000")
    else:
        run = paragraph.add_run(text)
        set_run_font(run, color="000000")


def fill_cover(doc: Document, code: str, module: dict):
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
                set_run_font(run, size=10.5, color="000000")


def write_brief(doc: Document, code: str, assignment_key: str, module: dict):
    title = ASSIGNMENTS[assignment_key]["title"].format(short=module["short"])
    replace_paragraph(doc.paragraphs[14], f"作业内容：{title}。", prefix="作业内容：")
    units = "、".join(item[0] for item in module["units"])
    if assignment_key == "pbl1_1":
        reqs = [
            f"（1）核心单元识别：围绕{module['short']}，说明{units}的工作原理、输入输出和适用问题。",
            f"（2）功能需求建模：以“{module['scenario']}”为场景，建立流程图、时序图或状态机，说明正常路径与异常路径。",
            "（3）单元交互与接口：定义关键接口、权限或一致性约束，说明如何避免数据错位、重复执行或结果身份混淆。（3分）",
        ]
        indices = [16, 17, 18]
        submit_index = 19
    elif assignment_key == "pbl1_2":
        reqs = [
            f"（1）平台问题分析：结合{module['short']}说明现有问题、性能或一致性风险。",
            "（2）架构方案：给出分层或事件驱动的组件架构，说明职责边界、数据流和技术选型。",
            "（3）关键组件：给出核心算法伪代码或数据模型，说明异常处理和可复现约束。",
            f"（4）创新设计：围绕“{module['innovation']}”论证收益、成本与可行性。",
        ]
        indices = [16, 17, 18, 19]
        submit_index = 20
    elif assignment_key == "pbl2_1":
        reqs = [
            f"（1）业务逻辑：分析{module['short']}的用户、关键业务步骤及与其他模块的关系。",
            "（2）需求分析：明确功能、准确性、性能、安全或可用性需求，并给出可检查的验收标准。",
            "（3）产品方案：给出业务流程、模块划分、技术选型、验收用例和创新点，说明方案边界。",
        ]
        indices = [16, 17, 18]
        submit_index = 19
    else:
        reqs = [
            f"（1）业务单元与原理：识别{module['short']}的主要业务单元，说明原理和适用问题。",
            "（2）软件组件转化：设计组件架构，定义接口契约、输入输出、错误语义和交互方式。",
            "（3）技术实现与验证：说明关键技术、伪代码或数据模型，并用测试要点证明组件可用且可核对。",
        ]
        indices = [16, 17, 18]
        submit_index = 19
    for index, text in zip(indices, reqs):
        replace_paragraph(doc.paragraphs[index], text)
    replace_paragraph(doc.paragraphs[submit_index], ASSIGNMENTS[assignment_key]["submission"], prefix="提交物：")


def style_answer_styles(doc: Document):
    for style_name, size, bold in [("Title", 16, True), ("Heading 1", 12, True), ("Heading 2", 11, True)]:
        try:
            style = doc.styles[style_name]
        except KeyError:
            style = doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = doc.styles["Normal"]
        style.font.name = FONT_NAME
        style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT_NAME)
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = RGBColor(0, 0, 0)


def add_body(doc: Document, text: str, bold_lead: str | None = None):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_lead and text.startswith(bold_lead):
        run = paragraph.add_run(bold_lead)
        set_run_font(run, size=10.5, bold=True, color="000000")
        run = paragraph.add_run(text[len(bold_lead):])
        set_run_font(run, size=10.5, color="000000")
    else:
        run = paragraph.add_run(text)
        set_run_font(run, size=10.5, color="000000")
    return paragraph


def add_heading(doc: Document, text: str, level: int = 1):
    paragraph = doc.add_paragraph(text, style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(5)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_with_next = True
    for run in paragraph.runs:
        set_run_font(run, size=12 if level == 1 else 11, bold=True, color="000000")
    return paragraph


def shade_cell(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=45, start=75, bottom=45, end=75):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color: str = "D9D9D9", size: int = 6):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), str(size))
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), color)


def add_table(doc: Document, headers: list[str], rows: list[tuple], widths: list[float] | None = None, font_size: float = 9.0):
    table = doc.add_table(rows=1, cols=len(headers))
    set_table_borders(table)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for col, header in enumerate(headers):
        cell = table.rows[0].cells[col]
        cell.text = header
        shade_cell(cell, "1F4E78")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                set_run_font(run, size=font_size, bold=True, color="FFFFFF")
    for row_index, values in enumerate(rows, start=1):
        cells = table.add_row().cells
        for col, value in enumerate(values):
            cell = cells[col]
            cell.text = str(value)
            if row_index % 2 == 0:
                shade_cell(cell, "EAF2F8")
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if col == 0 else WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    set_run_font(run, size=font_size, color="000000")
    if widths:
        for row in table.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_pseudocode(doc: Document, lines: list[str]):
    table = doc.add_table(rows=1, cols=1)
    set_table_borders(table, color="B7C9D6", size=6)
    cell = table.cell(0, 0)
    shade_cell(cell, "F3F4F6")
    set_cell_margins(cell, top=110, start=150, bottom=110, end=150)
    cell.text = "\n".join(f"{index + 1:02d}  {line}" for index, line in enumerate(lines))
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        for run in paragraph.runs:
            set_run_font(run, size=8.8, color="000000", font="Courier New")
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def draw_flow(module: dict, assignment_key: str, output: Path):
    labels = module["flows"][assignment_key]
    image = Image.new("RGB", (1700, 430), "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(DIAGRAM_FONT_PATH, 50, index=0)
    body_font = ImageFont.truetype(DIAGRAM_FONT_PATH, 34, index=0)
    note_font = ImageFont.truetype(DIAGRAM_FONT_PATH, 28, index=0)
    colors = ["#EAF2F8", "#D6EAF8", "#D5F5E3", "#FCF3CF", "#FADBD8"]
    title = module["name"]
    title_box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((1700 - (title_box[2] - title_box[0])) / 2, 20), title, fill="#000000", font=title_font)
    n = len(labels)
    box_w = 250
    box_h = 125
    left = 55
    gap = (1700 - 2 * left - n * box_w) / (n - 1)
    y0 = 145
    for index, label in enumerate(labels):
        x0 = int(left + index * (box_w + gap))
        x1 = x0 + box_w
        y1 = y0 + box_h
        draw.rounded_rectangle((x0, y0, x1, y1), radius=22, fill=colors[index % len(colors)], outline="#1F4E78", width=4)
        if len(label) > 8:
            split = math.ceil(len(label) / 2)
            shown = label[:split] + "\n" + label[split:]
        else:
            shown = label
        text_box = draw.multiline_textbbox((0, 0), shown, font=body_font, spacing=5, align="center")
        text_w = text_box[2] - text_box[0]
        text_h = text_box[3] - text_box[1]
        draw.multiline_text((x0 + (box_w - text_w) / 2, y0 + (box_h - text_h) / 2 - 4), shown, fill="#111111", font=body_font, spacing=5, align="center")
        if index < n - 1:
            next_x0 = int(left + (index + 1) * (box_w + gap))
            start = (x1 + 12, y0 + box_h // 2)
            end = (next_x0 - 18, y0 + box_h // 2)
            draw.line((start, end), fill="#5B6573", width=6)
            draw.polygon([(end[0], end[1]), (end[0] - 22, end[1] - 14), (end[0] - 22, end[1] + 14)], fill="#5B6573")
    note = "输入与结果均绑定版本或完整 Run ID，异常不静默补值"
    note_box = draw.textbbox((0, 0), note, font=note_font)
    draw.text(((1700 - (note_box[2] - note_box[0])) / 2, 360), note, fill="#444444", font=note_font)
    image.save(output, format="PNG", optimize=True)


def add_figure(doc: Document, path: Path, caption: str):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(1)
    run = paragraph.add_run()
    run.add_picture(str(path), width=Inches(5.85))
    caption_p = doc.add_paragraph(caption)
    caption_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p.paragraph_format.space_after = Pt(4)
    for run in caption_p.runs:
        set_run_font(run, size=9, color="444444")


def add_answer_title(doc: Document, module: dict, assignment_key: str):
    title = ASSIGNMENTS[assignment_key]["title"].format(short=module["short"])
    paragraph = doc.add_paragraph(title, style="Title")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_with_next = True
    for run in paragraph.runs:
        set_run_font(run, size=16, bold=True, color="000000")
    meta = doc.add_paragraph(f"项目：量化投资多因子研发平台    个人模块：{module['name']}")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_after = Pt(5)
    for run in meta.runs:
        set_run_font(run, size=9.5, color="555555")


def build_pbl1_1(doc: Document, module: dict, diagram: Path):
    add_answer_title(doc, module, "pbl1_1")
    add_heading(doc, "一 设计范围与核心单元")
    add_body(doc, f"本设计聚焦{module['name']}。目标是在单机私域部署和少量研究人员场景下，形成边界清晰、状态可追踪、结果可复核的功能闭环。{module['scenario']}")
    add_table(doc, ["核心单元", "工作原理", "输入输出", "关键约束"], module["units"], [1.0, 2.0, 1.5, 1.7], font_size=8.5)
    add_heading(doc, "二 典型流程模型")
    add_figure(doc, diagram, "图1 典型功能流程与模块交互")
    next_page = add_heading(doc, "三 交互求解过程")
    next_page.paragraph_format.page_break_before = True
    steps = [part.strip() for part in module["scenario"].replace("；", "。").split("。") if part.strip()]
    for index, step in enumerate(steps, start=1):
        add_body(doc, f"步骤{index}：{step}。")
    add_heading(doc, "四 关键接口与一致性设计")
    add_table(doc, ["接口或交互", "输入", "输出", "约束"], module["interfaces"], [1.45, 1.45, 1.45, 1.9], font_size=8.6)
    add_heading(doc, "五 异常处理与结论")
    add_body(doc, f"异常处理遵循“明确失败、保留证据、禁止静默修正”的原则。{module['tests']} 本设计把单元职责、接口和验收证据对应起来，能够支持后续实现与个人模块答辩。")


def build_pbl1_2(doc: Document, module: dict, diagram: Path):
    add_answer_title(doc, module, "pbl1_2")
    add_heading(doc, "一 问题场景与设计目标")
    add_body(doc, module["problem"])
    add_body(doc, f"设计目标是：在不引入不必要微服务复杂度的前提下，实现职责隔离、可复现、可审计和可部署。{module['architecture']}")
    add_heading(doc, "二 组件架构")
    add_figure(doc, diagram, "图1 关键组件架构与数据流")
    add_heading(doc, "三 组件职责")
    add_table(doc, ["组件", "职责"], [(name, detail) for name, detail, _, _ in module["units"]], [1.55, 4.6], font_size=9.0)
    next_page = add_heading(doc, "四 关键算法伪代码")
    next_page.paragraph_format.page_break_before = True
    add_pseudocode(doc, module["algorithm"])
    add_heading(doc, "五 数据与接口模型")
    add_table(doc, ["接口", "输入", "输出", "约束"], module["interfaces"], [1.5, 1.4, 1.4, 1.9], font_size=8.6)
    add_heading(doc, "六 创新点与可行性")
    add_body(doc, module["innovation"])
    add_table(doc, ["评价维度", "结论"], [
        ("收益", "提高结果可追踪性，减少手工核对和口径混淆。"),
        ("成本", "复用现有模块化单体和测试工具，不新增独立微服务运维。"),
        ("风险", "仍需对真实数据许可、样本偏差和最终人工验收单独说明。"),
    ], [1.2, 5.0], font_size=9.0)


def build_pbl2_1(doc: Document, module: dict, diagram: Path):
    add_answer_title(doc, module, "pbl2_1")
    add_heading(doc, "一 产品背景与业务逻辑")
    add_body(doc, module["business"])
    add_body(doc, f"典型业务闭环为：{module['scenario']} 产品不连接真实资金账户，不输出买卖建议，定位为研究工具。")
    add_heading(doc, "二 业务流程")
    add_figure(doc, diagram, "图1 产品业务流程")
    add_heading(doc, "三 功能与非功能需求")
    add_table(doc, ["类别", "需求", "验收标准"], module["requirements"], [0.9, 2.2, 3.1], font_size=8.8)
    next_page = add_heading(doc, "四 产品方案")
    next_page.paragraph_format.page_break_before = True
    add_body(doc, module["architecture"])
    add_body(doc, f"技术选择与课程规模匹配：{module['tech']}")
    add_heading(doc, "五 验收用例")
    add_table(doc, ["编号", "场景", "预期结果"], module["acceptance"], [0.9, 2.45, 2.85], font_size=8.8)
    add_heading(doc, "六 创新点与边界")
    add_body(doc, module["innovation"])
    add_body(doc, "边界：当前结论只证明软件流程、计算口径和交付一致性；数据来源授权、策略未来有效性、Windows 实机部署和队长最终人工产品测试需按实际证据另行记录。")


def build_pbl2_2(doc: Document, module: dict, diagram: Path):
    add_answer_title(doc, module, "pbl2_2")
    add_heading(doc, "一 业务单元到软件组件")
    add_body(doc, f"本模块将业务职责转化为四类软件组件：{'、'.join(module['components'])}。组件只通过明确输入输出协作，避免页面、计算和存储互相越界。")
    add_table(doc, ["业务单元", "业务原理", "软件边界"], [(name, detail, constraint) for name, detail, _, constraint in module["units"]], [1.25, 2.8, 2.3], font_size=8.7)
    add_heading(doc, "二 组件架构")
    add_figure(doc, diagram, "图1 组件架构与调用方向")
    add_heading(doc, "三 技术选型")
    add_body(doc, module["tech"])
    next_page = add_heading(doc, "四 关键接口契约")
    next_page.paragraph_format.page_break_before = True
    add_table(doc, ["接口或方法", "输入", "输出", "错误与约束"], module["interfaces"], [1.45, 1.35, 1.4, 2.0], font_size=8.5)
    add_heading(doc, "五 关键实现思路")
    add_pseudocode(doc, module["algorithm"])
    add_heading(doc, "六 测试与创造性解决方案")
    add_body(doc, module["tests"])
    add_body(doc, f"创造性方案：{module['innovation']} 该方案优先复用当前项目能力，避免为课程验收引入不可控依赖。")


BUILDERS = {
    "pbl1_1": build_pbl1_1,
    "pbl1_2": build_pbl1_2,
    "pbl2_1": build_pbl2_1,
    "pbl2_2": build_pbl2_2,
}


def build_document(code: str, module: dict, assignment_key: str) -> Path:
    template = TEMPLATES / TEMPLATE_FILES[assignment_key]
    if not template.exists():
        raise FileNotFoundError(template)
    title = ASSIGNMENTS[assignment_key]["title"].format(short=module["short"])
    output = FINAL / f"{code}_{module['short']}_{ASSIGNMENTS[assignment_key]['course']}_{ASSIGNMENTS[assignment_key]['label']}.docx"
    diagram = ASSETS / f"{code}_{assignment_key}_diagram.png"
    draw_flow(module, assignment_key, diagram)
    shutil.copy2(template, output)
    doc = Document(output)
    normalize_existing_fonts(doc)
    style_answer_styles(doc)
    fill_cover(doc, code, module)
    write_brief(doc, code, assignment_key, module)
    # Converted templates already end with a hard page break. A continuous
    # section applies compact answer-page margins without inserting a blank page.
    answer_section = doc.add_section(WD_SECTION.CONTINUOUS)
    answer_section.top_margin = Inches(0.62)
    answer_section.bottom_margin = Inches(0.62)
    answer_section.left_margin = Inches(0.72)
    answer_section.right_margin = Inches(0.72)
    answer_section.header_distance = Inches(0.25)
    answer_section.footer_distance = Inches(0.25)
    BUILDERS[assignment_key](doc, module, diagram)
    doc.core_properties.title = title
    doc.core_properties.subject = "量化投资多因子研发平台个人 PBL 作业"
    doc.core_properties.author = f"{code}【待填写姓名】"
    doc.core_properties.comments = "成员基础信息使用占位符；提交前请填写姓名、学号、班级和任课教师。"
    doc.save(output)
    return output


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    for path in FINAL.glob("*.docx"):
        path.unlink()
    outputs = []
    for code, module in MODULES.items():
        for assignment_key in ASSIGNMENTS:
            outputs.append(build_document(code, module, assignment_key))
    print(f"built={len(outputs)}")
    for output in outputs:
        print(f"{output.relative_to(ROOT)}\t{output.stat().st_size}\t{sha256(output)}")


if __name__ == "__main__":
    main()
