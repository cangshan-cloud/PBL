from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "outputs" / "pbl-midterm-reports-2026-11-21" / "final"

MODULES = {
    "A": ("平台基础与任务运行", "backend/app/tasks.py"),
    "B": ("数据集管理与质量控制", "backend/app/services/datasets.py::import_csv"),
    "C": ("因子计算与研究检验", "backend/app/domain/research.py::evaluate"),
    "D": ("研究工作台与报告交付", "frontend/src/main.tsx::downloadReport"),
}

FIGURE_ASSETS = {
    "A": ("A_platform_architecture.png", "A_run_state_machine.png", "A_async_sequence.png", "A_module_integration.png", "A_permission_path.png", "A_recovery_path.png"),
    "B": ("B_data_quality_gate.png", "B_version_lineage.png"),
    "C": ("C_signal_return_alignment.png", "C_research_audit.png"),
    "D": ("D_run_delivery_identity.png", "D_request_identity.png"),
}

REQUIRED = {
    "PBL1": ("一 项目概述", "二 技术架构", "三 个人技术实现", "四 个人项目进展", "七 相关代码"),
    "PBL2": ("一 项目概述", "二 需求分析", "三 个人功能设计", "四 挑战与问题", "六 相关代码"),
}


def document_text(document: Document) -> str:
    chunks = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            chunks.extend(cell.text for cell in row.cells)
    return "\n".join(chunks)


def main() -> int:
    files = sorted(FINAL.glob("*.docx"))
    errors: list[str] = []
    if len(files) != 8:
        errors.append(f"expected 8 reports, found {len(files)}")

    expected = {
        f"{code}_{short}_{course}_中期报告.docx"
        for code, (short, _) in MODULES.items()
        for course in REQUIRED
    }
    actual = {path.name for path in files}
    for name in sorted(expected - actual):
        errors.append(f"missing {name}")
    for name in sorted(actual - expected):
        errors.append(f"unexpected {name}")

    for path in files:
        code = path.name[0]
        course = "PBL1" if "_PBL1_" in path.name else "PBL2"
        short, code_path = MODULES[code]
        try:
            with zipfile.ZipFile(path) as archive:
                bad = archive.testzip()
                if bad:
                    errors.append(f"{path.name}: corrupt member {bad}")
            document = Document(path)
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append(f"{path.name}: cannot open: {exc}")
            continue

        text = document_text(document)
        checks = {
            "project title": "量化投资多因子研发平台" in text,
            "module": short in text,
            "identity placeholder": "【待填写：" in text,
            "individual scope": "个人模块" in text,
            "code location": code_path in text,
            "diagram count": len(document.inline_shapes) >= (6 if code == "A" and course == "PBL1" else 5 if code == "A" else 4),
            "substantial content": len(text) >= (10_000 if code == "A" else 7_400),
            "design decisions": ("关键设计决策" in text or "组长架构决策" in text),
            "domain model": "数据与领域模型" in text,
            "risk controls": "风险与应对" in text,
            "deep design": "操作流程与完成标准" in text,
            "acceptance scenarios": "典型验收场景" in text,
            "design boundary": "阶段反思与设计边界" in text,
            "code evidence mapping": ("代码能力与证据映射" in text if course == "PBL1" else "产品接口契约" in text),
            "submission checklist": "最终验收与提交检查清单" in text,
        }
        if code == "A" and course == "PBL1":
            checks["leader architecture decisions"] = "组长架构决策" in text
            checks["leader project governance"] = "组长项目治理" in text
        if code == "A" and course == "PBL2":
            checks["leader delivery governance"] = "组长协同与交付组织" in text
        for heading in REQUIRED[course]:
            checks[f"heading {heading}"] = heading in text
        for label, ok in checks.items():
            if not ok:
                errors.append(f"{path.name}: missing/invalid {label}")

    if errors:
        print("PBL midterm report check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    for code, names in FIGURE_ASSETS.items():
        for name in names:
            path = FINAL.parent / "assets" / name
            if not path.is_file() or path.stat().st_size < 10_000:
                print(f"PBL midterm report check failed: missing figure {code}/{name}", file=sys.stderr)
                return 1
    print("PBL midterm report check passed: 8 reports, 4 modules, PBL1/PBL2 complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
