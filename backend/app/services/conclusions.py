from __future__ import annotations

from app.models import Run, RunStatus


def build_run_conclusion(run: Run, result: dict | None = None) -> dict:
    if result is None:
        if run.status != RunStatus.SUCCESS:
            raise ValueError("only successful runs have a research conclusion")
        artifact = next((item for item in run.artifacts if item.artifact_type == "metrics"), None)
        if artifact is None or artifact.content is None:
            raise ValueError("successful run is missing metrics artifact")
        result = artifact.content
    ic = _number(result.get("ic_mean"))
    rank_ic = _number(result.get("rank_ic_mean"))
    icir = _number(result.get("icir"))
    positive_ratio = _number(result.get("ic_positive_ratio"))
    long_short = _number(result.get("long_short_total_return"))
    long_short_net = _number(result.get("long_short_net_total_return"))
    transaction_cost_bps = _number(result.get("transaction_cost_bps"))
    turnover = _number(result.get("top_group_turnover"))
    date_count = len(result.get("ic_series", []))

    strength = _strength(abs(ic) if ic is not None else None)
    stability = _stability(abs(icir) if icir is not None else None, date_count)
    direction = "正向" if ic is not None and ic > 0 else "负向" if ic is not None and ic < 0 else "不明确"
    if date_count < 20:
        verdict = "有效截面不足，当前结果只能证明研究流程可运行，暂不支持评价因子有效性。"
        grade = "insufficient"
    else:
        verdict = f"在当前样本与参数下，因子与下一期收益呈{direction}{strength}关系，时间稳定性{stability}。"
        grade = "weak" if strength == "较弱" else "promising" if stability != "较弱" else "mixed"

    evidence = [
        f"IC均值为{_fmt(ic)}，Rank IC均值为{_fmt(rank_ic)}，覆盖{date_count}个有效截面。",
        f"ICIR为{_fmt(icir)}，IC为正比例为{_fmt(positive_ratio, percent=True)}。",
        f"最高组减最低组的累计收益为{_fmt(long_short, percent=True)}，未计交易费用与冲击成本。",
        f"按单边{_fmt(transaction_cost_bps)}个基点扣减换手成本后，多空累计收益为{_fmt(long_short_net, percent=True)}。",
        f"头部组平均换手率为{_fmt(turnover, percent=True)}；换手越高，实际可实现收益越容易被成本侵蚀。",
    ]
    limitations = [
        "当前指标是样本内描述性统计，未进行显著性检验，不能证明因果关系或未来有效性。",
        "分组收益为毛收益；成本后多空收益使用固定成本假设，尚未模拟融资融券、涨跌停、停牌和成交容量约束。",
        "结果依赖数据版本、股票池、日期范围、复权方式和预处理参数，修改任一口径都可能改变结论。",
    ]
    if run.experiment.dataset_version.dataset_key == "demo_daily":
        limitations.insert(0, "当前使用仓库合成演示数据，只能用于软件验收，不得形成真实市场或投资结论。")
    if date_count < 60:
        limitations.append("有效截面少于60个交易日，稳定性判断的样本基础较弱。")

    next_steps = [
        "替换为来源可追溯的真实A股历史数据，并记录数据授权、复权和停牌处理口径。",
        "在不重叠的时间区间进行样本外检验，并与反向因子或简单基准比较。",
        "使用更贴近实际账户的佣金、印花税、冲击成本和可交易性约束复测净收益。",
    ]
    if turnover is not None and turnover > 0.5:
        next_steps.append("当前换手率偏高，建议延长调仓周期或增加换手惩罚后复测。")

    return {
        "run_id": run.id,
        "experiment_name": run.experiment.name,
        "grade": grade,
        "headline": verdict,
        "evidence": evidence,
        "limitations": limitations,
        "next_steps": next_steps,
        "method": {
            "type": "deterministic_rule_template",
            "version": "1.0.0",
            "thresholds": {"weak_abs_ic_below": 0.02, "strong_abs_ic_from": 0.05, "stable_abs_icir_from": 1.0},
        },
        "disclaimer": "本草稿由固定规则生成，必须由研究人员复核；仅用于课程研究，不构成投资建议。",
    }


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _strength(value: float | None) -> str:
    if value is None or value < 0.02:
        return "较弱"
    if value < 0.05:
        return "中等"
    return "较强"


def _stability(value: float | None, date_count: int) -> str:
    if date_count < 20 or value is None or value < 0.5:
        return "较弱"
    if value < 1:
        return "中等"
    return "较高"


def _fmt(value: float | None, *, percent: bool = False) -> str:
    if value is None:
        return "无法计算"
    return f"{value * 100:.2f}%" if percent else f"{value:.4f}"
