export type NavLine = {
  label: string;
  color: string;
  points: { date: string; value: number }[];
};

export type AlignedNavLine = {
  label: string;
  color: string;
  segments: { index: number; value: number }[][];
  lastValue: number | null;
};

export type ChartInspectionRow = {
  date: string;
  values: { label: string; value: number | null }[];
  hasRecord: boolean;
};

export function navInspectionRows(lines: readonly NavLine[], knownDates: readonly string[] = []): ChartInspectionRow[] {
  const byLine = lines.map(line => new Map(line.points.map(point => [point.date, point.value])));
  const dates = [...new Set([...knownDates, ...lines.flatMap(line => line.points.map(point => point.date))])].sort();
  return dates.map(date => ({
    date,
    values: lines.map((line, index) => {
      const value = byLine[index].get(date);
      return { label: line.label, value: value !== undefined && Number.isFinite(value) ? value : null };
    }),
    hasRecord: byLine.some(points => points.has(date)),
  }));
}

export function icChartLines(series: readonly { date: string; ic: number | null; rank_ic: number | null }[]): NavLine[] {
  return [
    { label: "IC", color: "#3f765d", points: series.map(item => ({ date: item.date, value: item.ic ?? Number.NaN })) },
    { label: "Rank IC", color: "#d69043", points: series.map(item => ({ date: item.date, value: item.rank_ic ?? Number.NaN })) },
  ];
}

export function icInspectionRows(
  series: readonly { date: string; ic: number | null; rank_ic: number | null }[],
  knownDates: readonly string[] = [],
): { date: string; ic: number | null; rank_ic: number | null; hasRecord: boolean }[] {
  const byDate = new Map(series.map(item => [item.date, item]));
  return [...new Set([...knownDates, ...byDate.keys()])].sort().map(date => {
    const saved = byDate.get(date);
    return { date, ic: saved?.ic ?? null, rank_ic: saved?.rank_ic ?? null, hasRecord: saved !== undefined };
  });
}

export function interiorAllMissingDates(aligned: { dates: readonly string[]; lines: readonly AlignedNavLine[] }): string[] {
  const present = new Set(aligned.lines.flatMap(line => line.segments.flatMap(segment => segment.map(point => point.index))));
  if (present.size < 2) return [];
  let first = aligned.dates.length;
  let last = -1;
  for (const index of present) {
    if (index < first) first = index;
    if (index > last) last = index;
  }
  return aligned.dates.filter((_, index) => index > first && index < last && !present.has(index));
}

export function alignNavLines(lines: readonly NavLine[], knownDates: readonly string[] = []): { dates: string[]; lines: AlignedNavLine[] } {
  const dates = [...new Set([...knownDates, ...lines.flatMap(line => line.points.map(point => point.date))])].sort();
  return {
    dates,
    lines: lines.map(line => {
      const byDate = new Map(line.points.map(point => [point.date, point.value]));
      const segments: { index: number; value: number }[][] = [];
      let current: { index: number; value: number }[] = [];
      let lastValue: number | null = null;
      dates.forEach((date, index) => {
        const value = byDate.get(date);
        if (value === undefined || !Number.isFinite(value)) {
          if (current.length) segments.push(current);
          current = [];
          return;
        }
        current.push({ index, value });
        lastValue = value;
      });
      if (current.length) segments.push(current);
      return { label: line.label, color: line.color, segments, lastValue };
    }),
  };
}
