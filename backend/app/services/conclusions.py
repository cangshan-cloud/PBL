from __future__ import annotations

import math

from app.models import Run, RunStatus


def build_run_conclusion(run: Run, result: dict | None = None) -> dict:
    if result is None:
        if run.status != RunStatus.SUCCESS:
            raise ValueError("only successful runs have a research conclusion")
        artifact = next((item for item in run.artifacts if item.artifact_type == "metrics"), None)
        if artifact is None or artifact.content is None:
            raise ValueError("successful run is missing metrics artifact")
        result = artifact.content
    split = result.get("time_split")
    phase = split["validation"] if split else result
    ic = _number(phase.get("ic_mean"))
    rank_ic = _number(phase.get("rank_ic_mean"))
    icir = _number(phase.get("icir"))
    positive_ratio = _number(phase.get("ic_positive_ratio"))
    long_short = _number(result.get("long_short_total_return"))
    long_short_net = _number(result.get("long_short_net_total_return"))
    transaction_cost_bps = _number(result.get("transaction_cost_bps"))
    turnover = _number(result.get("top_group_turnover"))
    ic_series = result.get("ic_series") or []
    full_date_count = sum(_number(item.get("ic")) is not None for item in ic_series)
    date_count = int(phase["valid_ic_dates"]) if split else full_date_count
    missing_ic_days = len(ic_series) - full_date_count
    research_ic = _number(split["research"].get("ic_mean")) if split else None
    direction_reversal = bool(split and ic is not None and research_ic is not None and ic * research_ic < 0)

    strength = _strength(abs(ic) if ic is not None else None)
    stability = _stability(abs(icir) if icir is not None else None, date_count)
    direction = "正向" if ic is not None and ic > 0 else "负向" if ic is not None and ic < 0 else "不明确"
    if date_count < 20:
        verdict = ("验证期有效 IC 截面不足，时间切分结果不足以评价因子表现。" if split
                   else "有效截面不足，当前结果只能证明研究流程可运行，暂不支持评价因子有效性。")
        grade = "insufficient"
    else:
        verdict = (f"验证期回溯 IC 呈{direction}{strength}关系，时间稳定性{stability}；不代表前瞻有效性。" if split
                   else f"在当前样本与参数下，因子与下一期收益呈{direction}{strength}关系，时间稳定性{stability}。")
        grade = "weak" if strength == "较弱" else "promising" if stability != "较弱" else "mixed"
        if split and (date_count < 60 or direction_reversal) and grade == "promising":
            grade = "mixed"
    if direction_reversal:
        verdict += " 验证期与研究期 IC 方向相反。"

    evidence = [
        f"{'验证期' if split else ''}IC均值为{_fmt(ic)}，Rank IC均值为{_fmt(rank_ic)}，覆盖{date_count}个有效截面。",
        f"{'验证期' if split else ''}ICIR为{_fmt(icir)}，IC为正比例为{_fmt(positive_ratio, percent=True)}。",
        f"{'全区间' if split else ''}最高组减最低组的累计收益为{_fmt(long_short, percent=True)}，未计交易费用与冲击成本。",
        f"{'全区间' if split else ''}按单边{_fmt(transaction_cost_bps)}个基点扣减换手成本后，多空累计收益为{_fmt(long_short_net, percent=True)}。",
        f"{'全区间' if split else ''}头部组平均换手率为{_fmt(turnover, percent=True)}；换手越高，实际可实现收益越容易被成本侵蚀。",
    ]
    if long_short is None:
        evidence[2] = "没有可计算的最高组减最低组收益，本次不能评价多空表现。"
    if long_short_net is None:
        evidence[3] = "没有可计算的成本后多空收益，不能评价固定换手成本后的表现。"
    limitations = [
        "当前全区间指标是回溯描述性统计，未进行显著性检验，不能证明因果关系或未来有效性。",
        "分组收益为毛收益；成本后多空收益使用固定成本假设，尚未模拟融资融券、涨跌停、停牌和成交容量约束。",
        "结果依赖数据版本、股票池、日期范围、复权方式和预处理参数，修改任一口径都可能改变结论。",
    ]
    if run.experiment.dataset_version.dataset_key == "demo_daily":
        limitations.insert(0, "当前使用仓库合成演示数据，只能用于软件验收，不得形成真实市场或投资结论。")
    historical = run.experiment.parameters.get("mode") == "historical_hs300_2024"
    if historical:
        limitations.insert(0, "本研究按历史查询成分与交易状态筛选，但成分生效时点和数据来源仍需持续核验，不能宣称完全消除偏差或模拟真实成交。")
    if date_count < 60:
        limitations.append(f"{'验证期' if split else ''}有效截面少于60个交易日，稳定性判断的样本基础较弱。")
    if missing_ic_days:
        limitations.append(f"IC序列有{missing_ic_days}个交易日无法计算，已从有效截面和稳定性分档中排除。")
    skipped_group_days = result.get("group_skipped_constant_factor_days")
    if isinstance(skipped_group_days, int) and not isinstance(skipped_group_days, bool) and skipped_group_days > 0:
        limitations.append(f"有{skipped_group_days}个交易日全截面因子同值，未生成分组和多空收益；分组统计仅覆盖其余可分组日期。")
    insufficient_group_days = result.get("group_skipped_insufficient_sample_days")
    if isinstance(insufficient_group_days, int) and not isinstance(insufficient_group_days, bool) and insufficient_group_days > 0:
        limitations.append(f"有{insufficient_group_days}个交易日有效证券数少于目标分组数，未生成分组和多空收益。")
    if result.get("long_short_series") == []:
        limitations.append("本次没有有效可分组日期，多空收益和换手率均不可计算；不得把缺失值解释为零收益。")
    if result.get("zero_observation_days", 0):
        limitations.append(f"所选市场日期中有{result['zero_observation_days']}天未形成任何有效因子与次日收益观测；不能凭覆盖差额推断具体停牌或缺行原因。")
    if split:
        evidence.append(f"研究期 IC 均值{_fmt(research_ic)}；验证期始于{split['validation_start_date']}，边界前一信号日已隔离。全区间 IC 均值{_fmt(_number(result.get('ic_mean')))}仅作背景。")
        limitations.append("时间切分是回溯诊断；若在查看验证结果后再次选择日期或因子，则不再是独立样本外检验。")
        if direction_reversal:
            limitations.append("研究期与验证期 IC 方向相反；不能用全区间均值掩盖这一差异。")

    next_steps = [
        ("核对历史成员生效时点、数据授权及复权/停牌口径，并复验封存包。" if historical
         else "替换为来源可追溯的真实A股历史数据，并记录数据授权、复权和停牌处理口径。"),
        ("固定因子与切分日期后，用更新的未见数据再次验证，并与简单基准比较。" if result.get("time_split")
         else "在不重叠的时间区间进行样本外检验，并与反向因子或简单基准比较。"),
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
            "version": "1.0.3" if split else "1.0.2",
            "grade_basis": "validation_ic" if split else "full_range_ic",
            "thresholds": {"weak_abs_ic_below": 0.02, "strong_abs_ic_from": 0.05, "stable_abs_icir_from": 1.0},
        },
        "disclaimer": "本草稿由固定规则生成，必须由研究人员复核；仅用于课程研究，不构成投资建议。",
    }


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


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
