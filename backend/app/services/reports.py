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
COVERAGE_STATUS_LABELS = {"valid": "可计算", "insufficient_sample": "样本不足",
                          "no_observation": "无有效观测", "constant_factor": "因子同值",
                          "constant_factor_or_return": "常量截面"}


def _dataset_risk_disclosures(dataset, parameters: dict | None = None) -> list[str]:
    report = dataset.quality_report or {}
    warnings: list[str] = []
    known_demo = (
        dataset.dataset_key == "demo_daily"
        and dataset.version == "0.2.0"
        and dataset.checksum == "c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e"
    )
    if known_demo or (dataset.dataset_key == "demo_daily" and report.get("source") == "bundled_demo"):
        warnings.append("该版本为内置合成演示数据，按工作日生成而非真实沪深交易日历；研究结果仅供软件功能验收，不能作为真实市场证据。")
    elif isinstance(report.get("columns"), list) and report.get("dataset_kind") != "hs300_bundle_v1":
        warnings.append(
            "该版本为 CSV 导入数据；平台的格式与已知日期异常检查不认证数据真实性、使用授权或完整交易日历，"
            "请结合原始来源和交易所记录复核。"
        )
    adapter = report.get("adapter_report")
    if isinstance(adapter, dict):
        flags = adapter.get("source_adjustment_flags")
        flag_names = {"1": "后复权", "2": "前复权", "3": "不复权"}
        if isinstance(flags, list) and len(flags) == 1 and isinstance(flags[0], str) and flags[0] in flag_names:
            flag = flags[0]
            warnings.append(
                f"适配来源记录 adjustflag={flag}（来源声明的{flag_names[flag]}状态）；"
                "此值仅为来源元数据，不是数值复权因子，任务默认直接使用导入的 close。请核对原始数据源的价格口径。"
            )
    if report.get("weekend_row_count", 0) > 0:
        warnings.append(f"质量报告含 {report['weekend_row_count']} 行周末日期行情，请核对源文件。")
    if report.get("announced_weekday_closure_row_count", 0) > 0:
        dates = report.get("announced_weekday_closure_dates") or []
        date_detail = f"（日期：{'、'.join(dates)}）" if dates else ""
        warnings.append(
            f"质量报告含 {report['announced_weekday_closure_row_count']} 行沪深交易所公告休市工作日行情{date_detail}；"
            f"规则版本：{report.get('announced_closure_calendar_version') or '未知'}。"
        )
    if report.get("calendar_uncovered_years"):
        warnings.append(f"离线公告休市规则未覆盖 {'、'.join(map(str, report['calendar_uncovered_years']))} 年；不能把零命中解释为日期合规。")
    missing_counts = report.get("missing_counts")
    if (isinstance(parameters, dict) and parameters.get("price_basis") == "factor_adjusted"
            and isinstance(missing_counts, dict)):
        missing_adj_factor = missing_counts.get("adj_factor")
        if isinstance(missing_adj_factor, int) and not isinstance(missing_adj_factor, bool) and missing_adj_factor > 0:
            warnings.append(
                f"该数据版本全量质量报告有 {missing_adj_factor} 行缺失 adj_factor；"
                "本次调整价研究只证明所选样本通过执行期乘数校验，不代表版本内其他证券可用于调整价研究。"
            )
    return warnings


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
        f'<div class="legend">{"".join(legends)}</div>'
        '<small>横向按已知结果/诊断日期等距，非自然日间隔；已知缺日断线。</small></figure>'
    )


def _align_dated_chart_series(
    series: list[tuple[str, list[dict], str, str]], known_dates: tuple[str, ...] = (),
) -> tuple[list[str], list[tuple[str, list[float | None], str]]]:
    """Align saved series and known diagnostic dates before SVG rendering."""
    dates = sorted(set(known_dates) | {str(point["date"]) for _, points, _, _ in series for point in points})
    aligned = []
    for label, points, value_key, color in series:
        by_date = {str(point["date"]): point.get(value_key) for point in points}
        aligned.append((label, [by_date.get(date) for date in dates], color))
    return dates, aligned


def _daily_series_detail(result: dict) -> str:
    """Show saved chart values and known sample dates without filling gaps."""
    ic_by_date = {str(item["date"]): item for item in result.get("ic_series", [])}
    nav_by_date = {str(item["date"]): item for item in result.get("long_short_series", [])}
    coverage_by_date = {str(item["date"]): item for item in result.get("daily_coverage", [])}
    group_maps = [
        (int(item["group"]), {str(point["date"]): point.get("nav") for point in item.get("points", [])})
        for item in result.get("group_nav", [])
    ]
    dates = sorted(set(ic_by_date) | set(nav_by_date) | set(coverage_by_date) |
                   {date for _, values in group_maps for date in values})
    if not dates:
        return ""
    group_headings = "".join(f"<th>Q{group} 净值</th>" for group, _ in group_maps)
    status_headings = "<th>IC 状态</th><th>分组状态</th>" if coverage_by_date else ""
    rows = []
    for date in dates:
        ic = ic_by_date.get(date, {})
        nav = nav_by_date.get(date, {})
        values = [ic.get("ic"), ic.get("rank_ic"), nav.get("nav"), nav.get("net_nav")]
        cells = "".join(f"<td>{_fmt(value)}</td>" for value in values)
        cells += "".join(f"<td>{_fmt(points.get(date))}</td>" for _, points in group_maps)
        if coverage_by_date:
            diagnostic = coverage_by_date.get(date, {})
            cells += "".join(
                f"<td>{html.escape(COVERAGE_STATUS_LABELS.get(status, str(status))) if status is not None else '—'}</td>"
                for status in (diagnostic.get("ic_status"), diagnostic.get("group_status"))
            )
        rows.append(f"<tr><td>{html.escape(date)}</td>{cells}</tr>")
    return (
        f'<details class="series-detail"><summary>展开逐日序列核对表（{len(dates)} 个已知日期）</summary>'
        '<p>按保存序列与可用逐日诊断的日期并集排列；空缺显示“—”，不补零或前值。'
        '状态仅说明该日计算情况，不推断缺失原因。表内数值保留四位小数，'
        '完整精度请核对同 Run 结构化结果或逐日 CSV；窄屏可横向滚动。</p>'
        '<div class="series-table-wrap"><table><thead><tr><th>日期</th><th>IC</th><th>Rank IC</th>'
        f'<th>毛净值</th><th>成本后净值</th>{group_headings}{status_headings}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div></details>'
    )


def build_report_html(run: Run, result: dict) -> str:
    experiment = run.experiment
    dataset = experiment.dataset_version
    data_disclosures = _dataset_risk_disclosures(dataset, experiment.parameters)
    demo_disclosure = (
        '<div class="risk"><b>数据质量与来源限制</b>'
        + "".join(f"<p>{html.escape(item)}</p>" for item in data_disclosures)
        + "</div>"
        if data_disclosures else ""
    )
    factor = experiment.factor_version
    parameters = html.escape(json.dumps(experiment.parameters, ensure_ascii=False, indent=2))
    groups = "".join(
        f"<tr><td>Q{int(item['group'])}</td><td>{_fmt(item['mean_return'], True)}</td>"
        f"<td>{_fmt(next((series['points'][-1]['nav'] for series in result.get('group_nav', []) if series['group'] == item['group'] and series['points']), None))}</td></tr>"
        for item in result.get("group_returns", [])
    )
    if not groups:
        groups = '<tr><td colspan="3">暂无可计算的分组收益；不以零收益填补。</td></tr>'
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
    known_dates = tuple(str(item["date"]) for item in result.get("daily_coverage", []))
    ic_dates, ic_series = _align_dated_chart_series([
        ("IC", ic_points, "ic", "#176548"),
        ("Rank IC", ic_points, "rank_ic", "#cc7b2c"),
    ], known_dates)
    ic_chart = _svg_chart(
        "每日 IC 与 Rank IC",
        ic_dates,
        ic_series,
        baseline=0,
    )
    nav_points = result.get("long_short_series", [])
    nav_dates, nav_series = _align_dated_chart_series([
        ("毛净值", nav_points, "nav", "#176548"),
        ("成本后净值", nav_points, "net_nav", "#cc7b2c"),
    ], known_dates)
    nav_chart = _svg_chart(
        "多空组合净值（初值 1）",
        nav_dates,
        nav_series,
        baseline=1,
    )
    group_nav = result.get("group_nav", [])
    group_dates, group_series = _align_dated_chart_series(
        [
            (f"Q{int(item['group'])}", item.get("points", []), "nav",
             GROUP_COLORS[(int(item["group"]) - 1) % len(GROUP_COLORS)])
            for item in group_nav
        ],
        known_dates,
    )
    group_nav_chart = _svg_chart(
        "各组净值（初值 1）",
        group_dates,
        group_series,
        baseline=1,
    )
    daily_series_detail = _daily_series_detail(result)
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
        components = experiment.parameters.get("components", [])
        component_rows = "".join(
            f"<tr><td>{html.escape(str(item['key']))}</td><td>{html.escape(str(item['version']))}</td>"
            f"<td>{html.escape(str(item.get('lookback') or '当日'))}</td><td>{_fmt(item['weight'], True)}</td></tr>"
            for item in components
        )
        correlation_values = {
            (item["left"], item["right"]): item.get("correlation")
            for item in composite.get("correlation_matrix", [])
        }
        factor_keys = [str(item["key"]) for item in components]
        correlation_table = ""
        if factor_keys and correlation_values:
            headings = "".join(f"<th>{html.escape(key)}</th>" for key in factor_keys)
            matrix_rows = "".join(
                "<tr><th>" + html.escape(left) + "</th>" + "".join(
                    f"<td>{_fmt(correlation_values.get((left, right)))}</td>" for right in factor_keys
                ) + "</tr>"
                for left in factor_keys
            )
            correlation_table = (
                "<h3>因子相关矩阵</h3><p>共同有效样本上逐日计算截面 Pearson 相关系数，再对可计算交易日取算术平均；"
                "空值表示没有可计算的交易日。相关性不代表因果关系或独立增益。</p>"
                f"<table><thead><tr><th>因子</th>{headings}</tr></thead><tbody>{matrix_rows}</tbody></table>"
            )
        component_rows = (
            "<h2>三、组合成分</h2><table><thead><tr><th>因子标识</th><th>版本</th><th>窗口</th><th>权重</th></tr></thead>"
            f"<tbody>{component_rows}</tbody></table><p>共同样本覆盖量：{int(composite.get('common_coverage', 0))}。成分缺失值不填零，统一取交集。</p>"
            f"{correlation_table}"
        )
    historical = result.get("historical_audit")
    coverage_rows = "".join(
        f"<tr><td>{html.escape(str(item['date']))}</td>"
        f"<td>{'—' if item.get('candidate_symbols') is None else int(item['candidate_symbols'])}</td>"
        f"<td>{int(item['eligible_symbols'])}</td>"
        f"<td>{_fmt(item.get('coverage_ratio'), True)}</td>"
        f"<td>{'—' if item.get('excluded_symbols') is None else int(item['excluded_symbols'])}</td>"
        f"<td>{html.escape(COVERAGE_STATUS_LABELS.get(item['ic_status'], str(item['ic_status'])))}</td>"
        f"<td>{html.escape(COVERAGE_STATUS_LABELS.get(item['group_status'], str(item['group_status'])))}</td></tr>"
        for item in result.get("daily_coverage", [])
    )
    coverage_section = (
        "<h2>逐日样本诊断</h2>"
        f"<p>候选证券日 {int(result.get('candidate_coverage', 0))}，有效观测 {int(result.get('coverage', 0))}，"
        f"总体覆盖率 {_fmt(result.get('coverage_ratio'), True)}，零观测日 {int(result.get('zero_observation_days', 0))}。</p>"
        "<p>候选数为所选样本当日可见的原始证券记录（历史包为当日成员）；"
        "有效数为已形成有限因子及次日收益的观测。回看预热日和末尾无次日标签日也可能形成差额；差额不等同停牌或缺行，"
        "准确原因须查数据质量或历史审计。无候选证券时比例不可计算。</p>"
        "<table><thead><tr><th>日期</th><th>候选</th><th>有效</th><th>覆盖率</th><th>未形成观测</th><th>IC状态</th><th>分组状态</th></tr></thead>"
        f"<tbody>{coverage_rows}</tbody></table>"
    ) if coverage_rows else ""
    time_split = result.get("time_split")
    split_section = ""
    if time_split:
        split_rows = "".join(
            f"<tr><td>{label}</td><td>{html.escape(item['start_date'])} 至 {html.escape(item['end_date'])}</td>"
            f"<td>{int(item['observation_count'])}</td><td>{int(item['valid_ic_dates'])}</td>"
            f"<td>{_fmt(item['ic_mean'])}</td><td>{_fmt(item['rank_ic_mean'])}</td>"
            f"<td>{_fmt(item['icir'])}</td><td>{_fmt(item['ic_positive_ratio'], True)}</td></tr>"
            for label, item in (("研究期", time_split["research"]), ("验证期", time_split["validation"]))
        )
        split_section = (
            "<h2>时间切分 IC 诊断</h2>"
            f"<p>验证期始于 {html.escape(time_split['validation_start_date'])}；"
            f"边界前 {html.escape(time_split['embargo_signal_date'])} 信号日隔离，不参与任何阶段。"
            "这是事先填写日期的回溯时间分段，不证明前瞻预测能力；仅比较 IC，不重算可交易收益。</p>"
            "<table><thead><tr><th>阶段</th><th>日期</th><th>观测</th><th>有效 IC 日</th>"
            "<th>IC 均值</th><th>Rank IC</th><th>ICIR</th><th>IC 为正</th></tr></thead>"
            f"<tbody>{split_rows}</tbody></table>"
        )
    universe_risk = ("本研究按历史时点查询成分，但成分生效、停牌状态与来源数据仍需独立核验，不能宣称完全消除偏差。"
                     if historical else "若使用当前成分股回溯历史，可能存在幸存者偏差。")
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
body{{font-family:Inter,'PingFang SC','Microsoft YaHei',sans-serif;color:#173128;background:#f4f5ef;margin:0}}main{{max-width:900px;margin:0 auto;padding:56px 42px}}header{{border-bottom:4px solid #173128;padding-bottom:24px}}h1{{font-size:38px;margin:8px 0}}h2{{margin-top:36px;font-size:22px}}.tag{{font-size:11px;letter-spacing:2px;color:#6b7c73}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.metric,.meta{{background:white;border:1px solid #dfe5dc;border-radius:12px;padding:16px}}.metric b{{display:block;font-size:25px;margin-top:7px}}.meta-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.meta small{{display:block;color:#78877f;margin-bottom:5px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:11px;border-bottom:1px solid #e5e9e2;text-align:left}}th{{background:#173128;color:white}}pre{{white-space:pre-wrap;background:#173128;color:#e2eee7;padding:18px;border-radius:10px}}.risk{{background:#fff5db;border-left:4px solid #d5a22f;padding:16px}}figure{{margin:18px 0;padding:18px;background:white;border:1px solid #dfe5dc;border-radius:12px;break-inside:avoid}}figcaption{{font-weight:700;margin-bottom:8px}}svg{{display:block;width:100%;height:auto}}svg text{{font:11px sans-serif;fill:#68786f}}.legend{{display:flex;gap:18px;flex-wrap:wrap;font-size:12px}}.legend span{{display:inline-flex;align-items:center;gap:6px}}.legend i{{width:14px;height:3px;display:inline-block}}.histogram{{display:grid;gap:5px}}.hist-row{{display:grid;grid-template-columns:100px 1fr 36px;align-items:center;gap:10px;font-size:12px}}.hist-row div{{height:9px;background:#edf2eb;border-radius:5px}}.hist-row i{{display:block;height:100%;background:#176548;border-radius:5px}}.hist-row b{{text-align:right}}.series-detail{{margin:18px 0;padding:16px;background:white;border:1px solid #dfe5dc;border-radius:12px}}.series-detail summary{{cursor:pointer;font-weight:700}}.series-detail p{{font-size:12px;color:#68786f}}.series-table-wrap{{overflow-x:auto}}.series-table-wrap table{{min-width:680px;font-size:12px}}.series-table-wrap th,.series-table-wrap td{{white-space:nowrap}}footer{{margin-top:44px;color:#7b8982;font-size:12px}}@media print{{body{{background:white}}main{{padding:20px}}figure{{border-color:#bbb}}}}
</style></head><body><main>
<header><p class="tag">FACTORLAB · {report_kind}</p><h1>{html.escape(experiment.name)}</h1><p>报告由结构化研究结果自动生成，所有版本与参数均绑定到本次Run。价格口径：{price_basis_text}。</p></header>
{demo_disclosure}
<h2>一、研究摘要</h2><div class="grid"><div class="metric">有效观测<b>{int(result.get('coverage', 0))}</b></div><div class="metric">IC均值<b>{_fmt(result.get('ic_mean'))}</b></div><div class="metric">Rank IC<b>{_fmt(result.get('rank_ic_mean'))}</b></div><div class="metric">ICIR（未年化）<b>{_fmt(result.get('icir'))}</b></div><div class="metric">IC为正比例<b>{_fmt(result.get('ic_positive_ratio'), True)}</b></div><div class="metric">毛多空累计收益<b>{_fmt(result.get('long_short_total_return'), True)}</b></div><div class="metric">成本后多空累计收益<b>{_fmt(result.get('long_short_net_total_return'), True)}</b></div><div class="metric">单边成本假设<b>{_fmt(result.get('transaction_cost_bps'))} bps</b></div><div class="metric">多空日均毛收益<b>{_fmt(result.get('long_short_mean'), True)}</b></div><div class="metric">多空平均双边换手<b>{_fmt(result.get('long_short_turnover'), True)}</b></div><div class="metric">头部组换手率<b>{_fmt(result.get('top_group_turnover'), True)}</b></div></div>
<h2>二、因子定义</h2><div class="meta-grid"><div class="meta"><small>因子</small><b>{html.escape(factor.name)}</b></div><div class="meta"><small>版本</small><b>{html.escape(factor.version)}</b></div><div class="meta"><small>公式</small><b>{html.escape(factor.formula)}</b></div><div class="meta"><small>检验时点</small><b>t日因子 → t+1日收益</b></div></div><p>{html.escape(factor.description)}</p>
{component_rows}<h2>数据与复现信息</h2><div class="meta-grid"><div class="meta"><small>数据集</small><b>{html.escape(dataset.name)}</b></div><div class="meta"><small>数据版本</small><b>{html.escape(dataset.version)}</b></div><div class="meta"><small>数据校验和</small><b>{html.escape(dataset.checksum[:16])}…</b></div><div class="meta"><small>代码版本</small><b>{html.escape(experiment.code_version)}</b></div><div class="meta"><small>Run ID</small><b>{html.escape(run.id)}</b></div><div class="meta"><small>状态</small><b>success</b></div><div class="meta"><small>因子日期范围</small><b>{html.escape(str(sample.get('start_date') or '数据起点'))} 至 {html.escape(str(sample.get('end_date') or '数据终点'))}</b></div><div class="meta"><small>实际证券数量</small><b>{int(sample.get('resolved_symbol_count', dataset.symbol_count))}</b></div></div>
<h2>四、研究参数</h2><pre>{parameters}</pre><p><b>预处理口径：</b>{html.escape(preprocessing_text)}</p>
<h2>五、分组结果</h2><p>全截面因子同值而跳过分组的日期：{int(result.get('group_skipped_constant_factor_days', 0))} 天；有效证券数少于目标分组数而跳过的日期：{int(result.get('group_skipped_insufficient_sample_days', 0))} 天。上述日期均不计入分组及多空收益；IC 可计算时仍保留。</p><table><thead><tr><th>因子分组</th><th>平均下一日收益</th><th>期末净值</th></tr></thead><tbody>{groups}</tbody></table>{coverage_section}{split_section}
<h2>时间序列与分布图</h2><p>曲线使用本次 Run 保存的结构化序列；断点表示该日指标不可计算，不按零填补。</p>{ic_chart}{histogram_chart}{group_nav_chart}{nav_chart}{daily_series_detail}
<h2>六、结构化结论草稿</h2><div class="risk"><p><b>{html.escape(conclusion['headline'])}</b></p><h3>证据</h3><ul>{conclusion_evidence}</ul><h3>限制</h3><ul>{conclusion_limits}</ul><h3>建议下一步</h3><ol>{conclusion_next}</ol><p>{html.escape(conclusion['disclaimer'])}</p></div>
<h2>七、口径与风险说明</h2><div class="risk"><p>本报告仅用于课程研究，不构成投资建议。样例或历史统计结果不能保证未来表现。</p><ul><li>因子在交易日收盘后形成，最早用于下一交易日收益检验。</li><li>ICIR为IC均值除以IC总体标准差，未做年化。</li><li>成本后收益仅按成员换手扣减固定单边成本，仍未模拟印花税差异、非线性冲击成本、涨跌停和停牌。</li><li>头部组换手率为相邻交易日最高因子组成员变化比例。</li><li>结果受样本范围、复权方式、停牌处理和数据质量影响。</li><li>{html.escape(universe_risk)}</li><li>财务类因子必须按照实际披露日期生效，避免前视偏差。</li></ul></div>
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
                "dataset_version_id": run.experiment.dataset_version.id,
                "dataset_checksum_sha256": run.experiment.dataset_version.checksum,
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


def report_delivery_copy(content: bytes, run: Run, archived_checksum: str) -> bytes:
    """Build a marked delivery copy without modifying the archived report bytes."""
    source = content.decode("utf-8")
    if "<main>" not in source:
        raise ValueError("归档报告缺少可插入披露说明的页面结构")
    dataset = run.experiment.dataset_version
    risks = _dataset_risk_disclosures(dataset, getattr(run.experiment, "parameters", None))
    if not risks:
        risks = ["数据来源和日历诊断仍需结合原始文件、授权和交易所记录核查；未命中已知异常不等于真实交易日认证。"]
    disclosure = (
        '<section style="background:#fff5db;border-left:4px solid #d5a22f;padding:16px;margin-bottom:20px">'
        '<strong>交付披露副本 · 非原始归档字节</strong>'
        + "".join(f"<p>{html.escape(risk)}</p>" for risk in risks)
        + f'<p>数据版本 ID：{html.escape(dataset.id)}；数据 SHA-256：{html.escape(dataset.checksum)}；'
        f'原始报告 SHA-256：{html.escape(archived_checksum)}。</p>'
        '</section>'
    )
    return source.replace("<main>", "<main>" + disclosure, 1).encode("utf-8")
