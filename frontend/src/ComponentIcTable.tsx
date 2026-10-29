export type ComponentIcRow = {
  factor: string;
  ic_mean: number | null;
  rank_ic_mean: number | null;
  valid_ic_dates: number;
  signal_date_count: number;
};

type Props = {
  rows?: ComponentIcRow[];
  factorName: (factor: string) => string;
};

function metric(value: number | null) {
  return value === null ? "—" : value.toFixed(4);
}

export function ComponentIcTable({ rows, factorName }: Props) {
  return <>
    <h3>成分因子同样本 IC</h3>
    <p>各因子先按自身原始可用截面预处理，再仅在共同有效的证券与日期上计算逐日 IC，并对有效日期取均值；不表示独立贡献或未来收益。</p>
    {rows?.length ? <div className="preview-scroll"><table><thead><tr><th>因子</th><th>IC 均值</th><th>Rank IC 均值</th><th>有效 IC 日</th></tr></thead><tbody>{rows.map(item => <tr key={item.factor}><td>{factorName(item.factor)}</td><td>{metric(item.ic_mean)}</td><td>{metric(item.rank_ic_mean)}</td><td>{item.valid_ic_dates}/{item.signal_date_count}</td></tr>)}</tbody></table></div> : <small>此归档任务未保存成分 IC 诊断。</small>}
  </>;
}
