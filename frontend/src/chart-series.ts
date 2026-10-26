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
