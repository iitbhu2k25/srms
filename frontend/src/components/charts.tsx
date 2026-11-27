"use client";

import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SERIES_COLORS } from "@/lib/colors";

export interface Series {
  key: string;
  label: string;
  unit?: string;
  points: { t: string; v: number | null }[];
  limitMin?: number | null;
  limitMax?: number | null;
}

/** Line chart for one or more series sharing the same timestamps. */
export default function TimeSeriesChart({ series, height = 260, showLimits = true }: {
  series: Series[]; height?: number; showLimits?: boolean;
}) {
  if (!series.length) return null;
  const rows = series[0].points.map((p, i) => {
    const row: Record<string, number | string | null> = { t: p.t };
    for (const s of series) row[s.key] = s.points[i]?.v ?? null;
    return row;
  });
  const spanH = (new Date(rows.at(-1)!.t as string).getTime() - new Date(rows[0].t as string).getTime()) / 3.6e6;
  const tick = (iso: string) => {
    const d = new Date(iso);
    return spanH <= 48
      ? d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
      : d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
  };
  const single = series.length === 1 ? series[0] : null;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="#eef1f5" vertical={false} />
        <XAxis dataKey="t" tickFormatter={tick} minTickGap={48} tick={{ fontSize: 11, fill: "#64748b" }} />
        <YAxis tick={{ fontSize: 11, fill: "#64748b" }} width={48} domain={["auto", "auto"]} />
        <Tooltip
          labelFormatter={(l) => new Date(String(l)).toLocaleString("en-IN")}
          formatter={(v, name) => {
            const s = series.find((x) => x.key === name);
            return [`${v} ${s?.unit ?? ""}`, s?.label ?? String(name)];
          }}
        />
        {series.length > 1 && <Legend formatter={(k) => series.find((s) => s.key === k)?.label ?? k} />}
        {showLimits && single?.limitMin != null && (
          <ReferenceLine y={single.limitMin} stroke="#dc2626" strokeDasharray="5 4" label={{ value: `min ${single.limitMin}`, fontSize: 10, fill: "#dc2626", position: "insideBottomRight" }} />
        )}
        {showLimits && single?.limitMax != null && (
          <ReferenceLine y={single.limitMax} stroke="#dc2626" strokeDasharray="5 4" label={{ value: `max ${single.limitMax}`, fontSize: 10, fill: "#dc2626", position: "insideTopRight" }} />
        )}
        {series.map((s, i) => (
          <Line key={s.key} type="monotone" dataKey={s.key} stroke={SERIES_COLORS[i % SERIES_COLORS.length]} dot={false} strokeWidth={1.8} isAnimationActive={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
