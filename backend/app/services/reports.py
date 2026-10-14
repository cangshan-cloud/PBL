from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Artifact, Run
from app.domain.research import ic_histogram
from app.services.conclusions import build_run_conclusion
from app.services.runs import get_run, list_runs


GROUP_COLORS = ("#277a5b", "#65a563", "#a5a944", "#d5a04b", "#b86e52", "#6d8bc3", "#805ca8", "#bc73aa", "#4e9ca3", "#707b7b")


def _fmt(value: float | int | None, percent: bool = False) -> str:
    if value is None:
        return "—"
    if percent:
        return f"{float(value) * 100:.2f}%"
    return f"{float(value):.4f}"


def _svg_chart(title: str, dates: list[str], series: list[tuple[str, list[float | None], str]], *, baseline: float) -> str:
    """Build a self-contained, print-friendly chart from saved result series."""
    if not dates:
        return f"<figure><figcaption>{html.escape(title)}</figcaption><p>暂无有效时间序列。</p></figure>"
    valid = [
        float(value)
        for _, values, _ in series
        for value in values
        if isinstance(value, (int, float)) and math.isfinite(value)
    ]
    if not valid:
        return f"<figure><figcaption>{html.escape(title)}</figcaption><p>暂无有效时间序列。</p></figure>"
    low, high = min([baseline, *valid]), max([baseline, *valid])
    if low == high:
        low -= 0.05
        high += 0.05
    padding = (high - low) * 0.08
    low -= padding
    high += padding

    def x(index: int) -> float:
        return 55 + index * 560 / max(1, len(dates) - 1)

    def y(value: float) -> float:
        return 190 - (value - low) * 165 / (high - low)

    paths = []
    legends = []
    for label, values, color in series:
        segments: list[list[str]] = []
        current: list[str] = []
        for index in range(len(dates)):
            value = values[index] if index < len(values) else None
            if isinstance(value, (int, float)) and math.isfinite(value):
                current.append(f"{x(index):.2f},{y(float(value)):.2f}")
            elif current:
                segments.append(current)
                current = []
        if current:
            segments.append(current)
        paths.extend(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(segment)}"/>'
            for segment in segments if len(segment) > 1
        )
        paths.extend(
            f'<circle cx="{point.split(",")[0]}" cy="{point.split(",")[1]}" r="3" fill="{color}"/>'
            for segment in segments if len(segment) == 1 for point in segment
        )
        legends.append(f'<span><i style="background:{color}"></i>{html.escape(label)}</span>')
    zero_line = y(baseline)
    return (
        f'<figure><figcaption>{html.escape(title)}</figcaption><svg viewBox="0 0 640 240" '
        f'role="img" aria-label="{html.escape(title)}" xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="55" y1="{zero_line:.2f}" x2="615" y2="{zero_line:.2f}" stroke="#b9c9be" stroke-dasharray="4 4"/>'
        f'<text x="4" y="30">{high:.3f}</text><text x="4" y="194">{low:.3f}</text>'
        f'{"".join(paths)}<text x="55" y="225">{html.escape(str(dates[0]))}</text>'
        f'<text x="615" y="225" text-anchor="end">{html.escape(str(dates[-1]))}</text></svg>'
        f'<div class="legend">{"".join(legends)}</div></figure>'
    )


def build_report_html(run: Run, result: dict) -> str:
    experiment = run.experiment
    dataset = experiment.dataset_version
    factor = experiment.factor_version
    parameters = html.escape(json.dumps(experiment.parameters, ensure_ascii=False, indent=2))
    groups = "".join(
        f"<tr><td>Q{int(item['group'])}</td><td>{_fmt(item['mean_return'], True)}</td>"
        f"<td>{_fmt(next((series['points'][-1]['nav'] for series in result.get('group_nav', []) if series['group'] == item['group'] and series['points']), None))}</td></tr>"
        for item in result.get("group_returns", [])
    )
    preprocessing = result.get("preprocessing", {})
    preprocessing_text = (
        f"MAD {preprocessing.get('mad_scale', 3)}倍去极值"
        if preprocessing.get("winsorize") else "不去极值"
    ) + ("，截面Z-score标准化" if preprocessing.get("standardize") else "，不标准化")
    composite = result.get("composite")
    sample = result.get("sample", {})
    price_basis_text = ("封存包源 close（BaoStock adjustflag=1）" if result.get("historical_audit")
                        else "close × adj_factor" if sample.get("price_basis") == "factor_adjusted" else "导入的 close")
    ic_points = result.get("ic_series", [])
    ic_chart = _svg_chart(
        "每日 IC 与 Rank IC",
        [str(item.get("date", "")) for item in ic_points],
        [("IC", [item.get("ic") for item in ic_points], "#176548"),
         ("Rank IC", [item.get("rank_ic") for item in ic_points], "#cc7b2c")],
        baseline=0,
    )
    nav_points = result.get("long_short_series", [])
    nav_chart = _svg_chart(
        "多空组合净值（初值 1）",
        [str(item.get("date", "")) for item in nav_points],
        [("毛净值", [item.get("nav") for item in nav_points], "#176548"),
         ("成本后净值", [item.get("net_nav") for item in nav_points], "#cc7b2c")],
        baseline=1,
    )
    group_nav = result.get("group_nav", [])
    longest_group = max(group_nav, key=lambda item: len(item.get("points", [])), default={})
    group_nav_chart = _svg_chart(
        "各组净值（初值 1）",
        [str(point.get("date", "")) for point in longest_group.get("points", [])],
        [
            (f"Q{int(item['group'])}", [point.get("nav") for point in item.get("points", [])], GROUP_COLORS[(int(item["group"]) - 1) % len(GROUP_COLORS)])
            for item in group_nav
        ],
        baseline=1,
    )
    histogram = result.get("ic_histogram")
    if histogram is None:
        histogram = ic_histogram([
            float(item["ic"]) for item in ic_points
            if isinstance(item.get("ic"), (int, float)) and math.isfinite(item["ic"])
        ])
    max_count = max((item["count"] for item in histogram), default=0) or 1
    histogram_rows = "".join(
        f'<div class="hist-row"><span>{item["lower"]:+.1f}～{item["upper"]:+.1f}</span>'
        f'<div><i style="width:{int(item["count"] / max_count * 100)}%"></i></div>'
        f'<b>{int(item["count"])}</b></div>'
        for item in histogram
    )
    histogram_chart = (
        '<figure><figcaption>IC 分布（固定 0.2 宽度分箱）</figcaption>'
        f'<div class="histogram">{histogram_rows}</div>'
        f'<p>有效交易日 {sum(int(item["count"]) for item in histogram)} 个；不可计算的 IC 不计入分布。</p></figure>'
    )
    conclusion = build_run_conclusion(run, result)
    conclusion_evidence = "".join(f"<li>{html.escape(item)}</li>" for item in conclusion["evidence"])
    conclusion_limits = "".join(f"<li>{html.escape(item)}</li>" for item in conclusion["limitations"])
    conclusion_next = "".join(f"<li>{html.escape(item)}</li>" for item in conclusion["next_steps"])
    report_kind = "MULTI FACTOR REPORT" if composite else "SINGLE FACTOR REPORT"
    component_rows = ""
    if composite:
        component_rows = "".join(
            f"<tr><td>{html.escape(str(item['key']))}</td><td>{html.escape(str(item['version']))}</td>"
            f"<td>{html.escape(str(item.get('lookback') or '当日'))}</td><td>{_fmt(item['weight'], True)}</td></tr>"
            for item in experiment.parameters.get("components", [])
        )
        component_rows = (
            "<h2>三、组合成分</h2><table><thead><tr><th>因子标识</th><th>版本</th><th>窗口</th><th>权重</th></tr></thead>"
            f"<tbody>{component_rows}</tbody></table><p>共同样本覆盖量：{int(composite.get('common_coverage', 0))}。成分缺失值不填零，统一取交集。</p>"
        )
    historical = result.get("historical_audit")
    if historical:
        audit_rows = "".join(
            f"<tr><td>{html.escape(key)}</td><td>{int(item['totals'].get('factor_signal', 0))}</td>"
            f"<td>{int(item['totals'].get('valid_return', 0))}</td>"
            f"<td>{int(item['totals'].get('invalid_contiguous_window', 0))}</td>"
            f"<td>{int(item['totals'].get('label_suspended', 0))}</td></tr>"
            for key, item in historical.items()
        )
        component_rows += (
            '<h2>历史样本与排除审计</h2><p>2024 年按日历史成分、停牌/ST 与成交量筛选；'
            '因子使用连续市场交易日窗口，收益仅取下一市场交易日。完整逐日计数见结构化结果。'
            '这只是条件研究检验，不是可成交回测，也不能宣称完全消除偏差。</p>'
            '<table><thead><tr><th>因子</th><th>有效因子信号</th><th>有效次日收益</th>'
            '<th>窗口无效</th><th>次日停牌</th></tr></thead><tbody>' + audit_rows + '</tbody></table>'
        )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(experiment.name)} · 因子研究报告</title>
<style>
body{{font-family:Inter,'PingFang SC','Microsoft YaHei',sans-serif;color:#173128;background:#f4f5ef;margin:0}}main{{max-width:900px;margin:0 auto;padding:56px 42px}}header{{border-bottom:4px solid #173128;padding-bottom:24px}}h1{{font-size:38px;margin:8px 0}}h2{{margin-top:36px;font-size:22px}}.tag{{font-size:11px;letter-spacing:2px;color:#6b7c73}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.metric,.meta{{background:white;border:1px solid #dfe5dc;border-radius:12px;padding:16px}}.metric b{{display:block;font-size:25px;margin-top:7px}}.meta-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.meta small{{display:block;color:#78877f;margin-bottom:5px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:11px;border-bottom:1px solid #e5e9e2;text-align:left}}th{{background:#173128;color:white}}pre{{white-space:pre-wrap;background:#173128;color:#e2eee7;padding:18px;border-radius:10px}}.risk{{background:#fff5db;border-left:4px solid #d5a22f;padding:16px}}figure{{margin:18px 0;padding:18px;background:white;border:1px solid #dfe5dc;border-radius:12px;break-inside:avoid}}figcaption{{font-weight:700;margin-bottom:8px}}svg{{display:block;width:100%;height:auto}}svg text{{font:11px sans-serif;fill:#68786f}}.legend{{display:flex;gap:18px;flex-wrap:wrap;font-size:12px}}.legend span{{display:inline-flex;align-items:center;gap:6px}}.legend i{{width:14px;height:3px;display:inline-block}}.histogram{{display:grid;gap:5px}}.hist-row{{display:grid;grid-template-columns:100px 1fr 36px;align-items:center;gap:10px;font-size:12px}}.hist-row div{{height:9px;background:#edf2eb;border-radius:5px}}.hist-row i{{display:block;height:100%;background:#176548;border-radius:5px}}.hist-row b{{text-align:right}}footer{{margin-top:44px;color:#7b8982;font-size:12px}}@media print{{body{{background:white}}main{{padding:20px}}figure{{border-color:#bbb}}}}
</style></head><body><main>
<header><p class="tag">FACTORLAB · {report_kind}</p><h1>{html.escape(experiment.name)}</h1><p>报告由结构化研究结果自动生成，所有版本与参数均绑定到本次Run。价格口径：{price_basis_text}。</p></header>
<h2>一、研究摘要</h2><div class="grid"><div class="metric">有效观测<b>{int(result.get('coverage', 0))}</b></div><div class="metric">IC均值<b>{_fmt(result.get('ic_mean'))}</b></div><div class="metric">Rank IC<b>{_fmt(result.get('rank_ic_mean'))}</b></div><div class="metric">ICIR（未年化）<b>{_fmt(result.get('icir'))}</b></div><div class="metric">IC为正比例<b>{_fmt(result.get('ic_positive_ratio'), True)}</b></div><div class="metric">毛多空累计收益<b>{_fmt(result.get('long_short_total_return'), True)}</b></div><div class="metric">成本后多空累计收益<b>{_fmt(result.get('long_short_net_total_return'), True)}</b></div><div class="metric">单边成本假设<b>{_fmt(result.get('transaction_cost_bps'))} bps</b></div><div class="metric">多空日均毛收益<b>{_fmt(result.get('long_short_mean'), True)}</b></div><div class="metric">多空平均双边换手<b>{_fmt(result.get('long_short_turnover'), True)}</b></div><div class="metric">头部组换手率<b>{_fmt(result.get('top_group_turnover'), True)}</b></div></div>
<h2>二、因子定义</h2><div class="meta-grid"><div class="meta"><small>因子</small><b>{html.escape(factor.name)}</b></div><div class="meta"><small>版本</small><b>{html.escape(factor.version)}</b></div><div class="meta"><small>公式</small><b>{html.escape(factor.formula)}</b></div><div class="meta"><small>检验时点</small><b>t日因子 → t+1日收益</b></div></div><p>{html.escape(factor.description)}</p>
{component_rows}<h2>数据与复现信息</h2><div class="meta-grid"><div class="meta"><small>数据集</small><b>{html.escape(dataset.name)}</b></div><div class="meta"><small>数据版本</small><b>{html.escape(dataset.version)}</b></div><div class="meta"><small>数据校验和</small><b>{html.escape(dataset.checksum[:16])}…</b></div><div class="meta"><small>代码版本</small><b>{html.escape(experiment.code_version)}</b></div><div class="meta"><small>Run ID</small><b>{html.escape(run.id)}</b></div><div class="meta"><small>状态</small><b>success</b></div><div class="meta"><small>因子日期范围</small><b>{html.escape(str(sample.get('start_date') or '数据起点'))} 至 {html.escape(str(sample.get('end_date') or '数据终点'))}</b></div><div class="meta"><small>实际证券数量</small><b>{int(sample.get('resolved_symbol_count', dataset.symbol_count))}</b></div></div>
<h2>四、研究参数</h2><pre>{parameters}</pre><p><b>预处理口径：</b>{html.escape(preprocessing_text)}</p>
<h2>五、分组结果</h2><table><thead><tr><th>因子分组</th><th>平均下一日收益</th><th>期末净值</th></tr></thead><tbody>{groups}</tbody></table>
<h2>时间序列与分布图</h2><p>曲线使用本次 Run 保存的结构化序列；断点表示该日指标不可计算，不按零填补。</p>{ic_chart}{histogram_chart}{group_nav_chart}{nav_chart}
<h2>六、结构化结论草稿</h2><div class="risk"><p><b>{html.escape(conclusion['headline'])}</b></p><h3>证据</h3><ul>{conclusion_evidence}</ul><h3>限制</h3><ul>{conclusion_limits}</ul><h3>建议下一步</h3><ol>{conclusion_next}</ol><p>{html.escape(conclusion['disclaimer'])}</p></div>
<h2>七、口径与风险说明</h2><div class="risk"><p>本报告仅用于课程研究，不构成投资建议。样例或历史统计结果不能保证未来表现。</p><ul><li>因子在交易日收盘后形成，最早用于下一交易日收益检验。</li><li>ICIR为IC均值除以IC总体标准差，未做年化。</li><li>成本后收益仅按成员换手扣减固定单边成本，仍未模拟印花税差异、非线性冲击成本、涨跌停和停牌。</li><li>头部组换手率为相邻交易日最高因子组成员变化比例。</li><li>结果受样本范围、复权方式、停牌处理和数据质量影响。</li><li>若使用当前成分股回溯历史，可能存在幸存者偏差。</li><li>财务类因子必须按照实际披露日期生效，避免前视偏差。</li></ul></div>
<footer>FactorLab自动报告 · Run {html.escape(run.id)} · 生成时间以任务完成时间为准</footer>
</main></body></html>"""


def create_report_artifact(run: Run, result: dict, data_root: Path) -> Artifact:
    content = build_report_html(run, result).encode("utf-8")
    report_dir = data_root / "artifacts" / run.id
    report_dir.mkdir(parents=True, exist_ok=True)
    target = report_dir / "factor_report.html"
    target.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()
    return Artifact(
        artifact_type="report_html",
        name="factor_report.html",
        content={"title": f"{run.experiment.name}研究报告", "media_type": "text/html"},
        storage_uri=str(target),
        checksum=checksum,
    )


def report_artifact(run: Run) -> Artifact | None:
    return next((item for item in run.artifacts if item.artifact_type == "report_html"), None)


def list_reports(session: Session, created_by_id: str | None = None) -> list[dict]:
    output = []
    for run in list_runs(session):
        if created_by_id is not None and run.experiment.created_by_id != created_by_id:
            continue
        artifact = report_artifact(run)
        if artifact is not None:
            output.append({
                "run_id": run.id,
                "experiment_name": run.experiment.name,
                "dataset_version": run.experiment.dataset_version.version,
                "factor_version": run.experiment.factor_version.version,
                "created_at": artifact.created_at,
                "checksum": artifact.checksum or "",
            })
    return output


def get_report(session: Session, run_id: str) -> tuple[Run, Artifact] | None:
    run = get_run(session, run_id)
    if run is None:
        return None
    artifact = report_artifact(run)
    return (run, artifact) if artifact is not None else None


def read_verified_report(artifact: Artifact) -> bytes:
    """Return exactly the report bytes whose digest was recorded at creation."""
    path = Path(artifact.storage_uri or "")
    if not path.is_file():
        raise FileNotFoundError("研究报告文件已丢失")
    content = path.read_bytes()
    if not artifact.checksum or hashlib.sha256(content).hexdigest() != artifact.checksum:
        raise ValueError("研究报告校验和不匹配，文件可能已被修改")
    return content
