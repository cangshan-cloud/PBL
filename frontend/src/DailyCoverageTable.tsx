import { useState } from "react";
import { selectCoveragePage } from "./daily-coverage";

export type DailyCoverageRow = {
  date: string;
  candidate_symbols?: number;
  eligible_symbols: number;
  excluded_symbols?: number;
  coverage_ratio?: number | null;
  ic_status: string;
  group_status: string;
};

type Props = {
  rows: DailyCoverageRow[];
  candidateCoverage?: number;
  coverage: number;
  coverageRatio?: number | null;
  zeroObservationDays?: number;
};

function percent(value: number | null | undefined) {
  return value == null ? "—" : `${(value * 100).toFixed(2)}%`;
}

export function DailyCoverageTable({ rows, candidateCoverage, coverage, coverageRatio, zeroObservationDays }: Props) {
  const [requestedPage, setRequestedPage] = useState(0);
  const current = selectCoveragePage(rows, requestedPage);
  return <section className="card comparison-table daily-coverage-table">
    <h2>逐日样本诊断</h2>
    <p>候选证券日 {candidateCoverage ?? "—"}，有效观测 {coverage}，总体覆盖率 {percent(coverageRatio)}；零观测日 {zeroObservationDays ?? "—"}。回看预热、末尾无次日标签也会造成差额；不能直接归因于停牌或缺行。</p>
    <div className="coverage-pager" role="group" aria-label="逐日样本诊断分页">
      <span aria-live="polite">显示第 {current.total ? current.start + 1 : 0}–{current.end} 日，共 {current.total} 日（第 {current.page + 1}/{current.pageCount} 页）</span>
      <div><button type="button" onClick={() => setRequestedPage(current.page - 1)} disabled={current.page === 0}>上一页</button><button type="button" onClick={() => setRequestedPage(current.page + 1)} disabled={current.page + 1 >= current.pageCount}>下一页</button></div>
    </div>
    <div className="preview-scroll"><table><thead><tr><th>日期</th><th>候选</th><th>有效</th><th>覆盖率</th><th>未形成观测</th><th>IC</th><th>分组</th></tr></thead><tbody>{current.rows.map(item => <tr key={item.date}><td>{item.date}</td><td>{item.candidate_symbols ?? "—"}</td><td>{item.eligible_symbols}</td><td>{percent(item.coverage_ratio)}</td><td>{item.excluded_symbols ?? "—"}</td><td>{item.ic_status === "valid" ? "可计算" : item.ic_status === "insufficient_sample" ? "样本不足" : item.ic_status === "no_observation" ? "无有效观测" : "常量截面"}</td><td>{item.group_status === "valid" ? "已分组" : item.group_status === "insufficient_sample" ? "样本不足" : item.group_status === "no_observation" ? "无有效观测" : "因子同值"}</td></tr>)}</tbody></table></div>
  </section>;
}
