"use client";

import { CartesianGrid, Legend, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Async, Card, PageHeader, StatusBadge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { SERIES_COLORS, STATUS_COLOR, rhiStatus } from "@/lib/colors";
import { fmtNum } from "@/lib/format";
import type { HealthHistoryPoint, StationLatest } from "@/lib/types";

const WEIGHTS = [
  ["Dissolved oxygen", "35%", "8 mg/L → 100, 2 mg/L → 0"],
  ["BOD", "20%", "2 mg/L → 100, 15 mg/L → 0"],
  ["Ammonium", "20%", "0.5 mg/L → 100, 5 mg/L → 0"],
  ["Turbidity", "10%", "10 NTU → 100, 80 NTU → 0"],
  ["pH", "10%", "6.5–8.5 → 100"],
  ["Conductivity", "5%", "750 µS/cm → 100, 2500 → 0"],
];

export default function HealthPage() {
  const history = useApi<HealthHistoryPoint[]>("/health-index/history?months=12");
  const stations = useApi<StationLatest[]>("/stations");

  const monthLabel = (m: string) => new Date(`${m}-01`).toLocaleDateString("en-IN", { month: "short", year: "2-digit" });

  return (
    <>
      <PageHeader
        title="River Health Index"
        subtitle="Composite 0–100 score from continuous IoT water-quality data. Issued monthly; the live value updates with every reading."
      />
      <div className="stack">
        <Card title="Basin RHI — last 12 months">
          <Async data={history.data} error={history.error}>
            {(h) => (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={h.map((x) => ({ ...x, ...x.by_station }))} margin={{ top: 8, right: 16, left: -10, bottom: 0 }}>
                  <ReferenceArea y1={80} y2={100} fill={STATUS_COLOR.good} fillOpacity={0.06} />
                  <ReferenceArea y1={60} y2={80} fill={STATUS_COLOR.moderate} fillOpacity={0.06} />
                  <ReferenceArea y1={40} y2={60} fill={STATUS_COLOR.poor} fillOpacity={0.06} />
                  <ReferenceArea y1={0} y2={40} fill={STATUS_COLOR.critical} fillOpacity={0.06} />
                  <CartesianGrid stroke="#eef1f5" vertical={false} />
                  <XAxis dataKey="month" tickFormatter={monthLabel} tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip labelFormatter={(m) => monthLabel(String(m))} />
                  <Legend />
                  <Line isAnimationActive={false} dataKey="rhi" name="Basin average" stroke="#0f172a" strokeWidth={3} dot={false} />
                  {Object.keys(h[0]?.by_station ?? {}).map((sid, i) => (
                    <Line key={sid} isAnimationActive={false} dataKey={sid} stroke={SERIES_COLORS[i % SERIES_COLORS.length]} strokeWidth={1.2} dot={false} strokeOpacity={0.7} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </Async>
        </Card>

        <div className="grid g-2">
          <Card title="Current score by station" flush>
            <Async data={stations.data} error={stations.error}>
              {(list) => (
                <table>
                  <thead><tr><th>Station</th><th>Status</th><th style={{ width: "40%" }}>RHI</th></tr></thead>
                  <tbody>
                    {list.map((s) => {
                      const st = rhiStatus(s.health_index);
                      return (
                        <tr key={s.id}>
                          <td><b>{s.id}</b> <span className="muted small">{s.name}</span></td>
                          <td><StatusBadge status={st} /></td>
                          <td>
                            <div className="row" style={{ flexWrap: "nowrap" }}>
                              <div className="bar" style={{ flex: 1 }}><span style={{ width: `${s.health_index}%`, background: STATUS_COLOR[st] }} /></div>
                              <b style={{ width: 36, textAlign: "right" }}>{fmtNum(s.health_index)}</b>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </Async>
          </Card>
          <Card title="How the index is calculated" sub="placeholder weights — to be finalised">
            <table>
              <thead><tr><th>Sub-index</th><th>Weight</th><th>Scoring</th></tr></thead>
              <tbody>{WEIGHTS.map(([a, b, c]) => <tr key={a}><td>{a}</td><td>{b}</td><td className="small muted">{c}</td></tr>)}</tbody>
            </table>
            <div className="row small" style={{ marginTop: 12, gap: 14 }}>
              <span><span className="dot" style={{ background: STATUS_COLOR.good }} /> ≥ 80 good</span>
              <span><span className="dot" style={{ background: STATUS_COLOR.moderate }} /> 60–80 moderate</span>
              <span><span className="dot" style={{ background: STATUS_COLOR.poor }} /> 40–60 poor</span>
              <span><span className="dot" style={{ background: STATUS_COLOR.critical }} /> &lt; 40 critical</span>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
