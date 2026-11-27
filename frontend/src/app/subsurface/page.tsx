"use client";

import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Map from "@/components/Map";
import { Async, Badge, Card, PageHeader } from "@/components/ui";
import { useApi } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { TemSection, TemTransect, Well, WellSeries } from "@/lib/types";

const EXCHANGE_COLOR = { gaining: "#16a34a", losing: "#ea580c", disconnected: "#64748b", unknown: "#94a3b8" };

// Resistivity colour scale (log): conductive clay / contaminated = warm, resistive sand = blue.
const STOPS: [number, [number, number, number]][] = [
  [0, [180, 20, 40]], [0.25, [240, 120, 40]], [0.45, [250, 220, 90]], [0.65, [120, 200, 140]], [0.85, [40, 130, 200]], [1, [30, 50, 140]],
];
const RHO_MIN = 3, RHO_MAX = 300;
function rhoColor(rho: number) {
  const t = Math.min(1, Math.max(0, Math.log10(rho / RHO_MIN) / Math.log10(RHO_MAX / RHO_MIN)));
  for (let i = 1; i < STOPS.length; i++) {
    if (t <= STOPS[i][0]) {
      const [t0, c0] = STOPS[i - 1], [t1, c1] = STOPS[i];
      const f = (t - t0) / (t1 - t0);
      return `rgb(${c0.map((c, j) => Math.round(c + (c1[j] - c) * f)).join(",")})`;
    }
  }
  return "rgb(30,50,140)";
}

function Section({ s }: { s: TemSection }) {
  const W = 900, H = 340, padL = 44, padB = 28, padT = 8;
  const xs = s.distances_m, zs = s.depths_m;
  const maxX = xs[xs.length - 1], maxZ = zs[zs.length - 1] + (zs[1] - zs[0]);
  const sx = (x: number) => padL + (x / maxX) * (W - padL - 10);
  const sz = (z: number) => padT + (z / maxZ) * (H - padT - padB);
  const cw = (W - padL - 10) / xs.length + 0.5, ch = (H - padT - padB) / zs.length + 0.5;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto" }}>
      {s.resistivity.map((row, i) => row.map((v, j) => (
        <rect key={`${i}-${j}`} x={padL + j * ((W - padL - 10) / xs.length)} y={sz(zs[i])} width={cw} height={ch} fill={rhoColor(v)}>
          <title>{`x ${xs[j]} m, z ${zs[i]} m: ${v} Ω·m`}</title>
        </rect>
      )))}
      {s.interpretation.map((it) => (
        <g key={it.label}>
          <rect x={sx(it.x_from)} y={sz(it.z_from)} width={sx(it.x_to) - sx(it.x_from)} height={sz(it.z_to) - sz(it.z_from)}
            fill="none" stroke="#0f172a" strokeDasharray="6 4" strokeWidth={1.5} />
          <text x={sx(it.x_from) + 6} y={sz(it.z_from) + 15} fontSize={13} fontWeight={600} fill="#0f172a">{it.label}</text>
        </g>
      ))}
      <line x1={sx(maxX / 2)} x2={sx(maxX / 2)} y1={padT - 4} y2={padT + 4} stroke="#0284c7" strokeWidth={6} />
      <text x={sx(maxX / 2) + 6} y={padT + 10} fontSize={11} fill="#0284c7">river</text>
      {[0, 20, 40, 60, 80, 100, 120].map((z) => (
        <text key={z} x={padL - 6} y={sz(z) + 4} fontSize={11} textAnchor="end" fill="#64748b">{z}</text>
      ))}
      {xs.filter((_, i) => i % 5 === 0).map((x) => (
        <text key={x} x={sx(x)} y={H - 8} fontSize={11} textAnchor="middle" fill="#64748b">{x}</text>
      ))}
      <text x={12} y={H / 2} fontSize={11} fill="#64748b" transform={`rotate(-90 12 ${H / 2})`} textAnchor="middle">depth (m)</text>
    </svg>
  );
}

export default function SubsurfacePage() {
  const transects = useApi<TemTransect[]>("/tem/transects");
  const [tid, setTid] = useState("TEM-T3");
  const section = useApi<TemSection>(`/tem/transects/${tid}/section`);
  const wells = useApi<Well[]>("/groundwater/wells", { refreshInterval: 60_000 });
  const [wid, setWid] = useState("GW-03");
  const ws = useApi<WellSeries>(`/groundwater/wells/${wid}/series?days=365`);

  const t = transects.data?.find((x) => x.id === tid);

  return (
    <>
      <PageHeader
        title="TEM geophysics & groundwater"
        subtitle="Annual pre-monsoon TEM transects map aquifer geometry, paleo-channels and contaminated zones; groundwater loggers sited from TEM results track river–aquifer exchange continuously."
      />
      <div className="grid g-main">
        <Card title="Resistivity section" sub={t ? `${t.name} · ${fmtDate(t.survey_date)} · ${t.length_m} m` : undefined}
          actions={<div className="row">{transects.data?.map((x) => (
            <button key={x.id} className={`chip ${x.id === tid ? "on" : ""}`} onClick={() => setTid(x.id)}>{x.id}</button>
          ))}</div>}>
          <Async data={section.data} error={section.error}>{(s) => <Section s={s} />}</Async>
          <div className="row small" style={{ marginTop: 6 }}>
            <span className="muted">Ω·m</span>
            <div style={{ flex: 1, maxWidth: 320, height: 10, borderRadius: 4, background: `linear-gradient(to right, ${[3, 6, 12, 25, 50, 100, 300].map(rhoColor).join(",")})` }} />
            <span className="muted">3 (clay / contaminated) → 300 (sand / gravel)</span>
          </div>
          {t && <p className="small" style={{ marginBottom: 0 }}><b>Interpretation:</b> {t.finding}</p>}
        </Card>
        <Card title="Transects & wells" flush>
          <Map height={420}
            lines={(transects.data ?? []).map((x) => ({ id: x.id, positions: [x.start, x.end], color: x.id === tid ? "#dc2626" : "#7c3aed", weight: 5, label: x.name }))}
            markers={(wells.data ?? []).map((w) => ({ id: w.id, lat: w.lat, lon: w.lon, color: EXCHANGE_COLOR[w.exchange], label: `${w.id} · ${w.exchange}` }))}
            center={[25.39, 82.78]} zoom={10} />
          <div className="map-legend">
            <span><span className="dot" style={{ background: "#dc2626" }} />selected transect</span>
            {Object.entries(EXCHANGE_COLOR).map(([k, c]) => <span key={k}><span className="dot" style={{ background: c }} />{k} well</span>)}
          </div>
        </Card>
      </div>

      <div className="grid g-2" style={{ marginTop: 16 }}>
        <Card title="Groundwater loggers" flush>
          <Async data={wells.data} error={wells.error}>
            {(list) => (
              <table>
                <thead><tr><th>Well</th><th>TEM zone</th><th className="num">Depth to water</th><th className="num">EC</th><th className="num">Head diff.</th><th>Exchange</th></tr></thead>
                <tbody>
                  {list.map((w) => (
                    <tr key={w.id} className="clickable" onClick={() => setWid(w.id)} style={w.id === wid ? { background: "#ecfeff" } : undefined}>
                      <td><b>{w.id}</b><div className="small muted">{w.name} · paired {w.paired_station}</div></td>
                      <td className="small">{w.zone}</td>
                      <td className="num">{w.latest.depth_to_water_m} m</td>
                      <td className="num">{w.latest.ec}</td>
                      <td className="num">{w.head_difference_m == null ? "—" : `${w.head_difference_m > 0 ? "+" : ""}${w.head_difference_m} m`}</td>
                      <td><Badge color={EXCHANGE_COLOR[w.exchange]}>{w.exchange}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Async>
        </Card>
        <Card title={`${wid} — river–aquifer head difference`} sub="last 12 months · +ve = aquifer feeds river">
          <Async data={ws.data} error={ws.error}>
            {(d) => (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={d.points} margin={{ top: 8, right: 12, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="#eef1f5" vertical={false} />
                  <XAxis dataKey="t" tickFormatter={(v) => new Date(v).toLocaleDateString("en-IN", { month: "short" })} minTickGap={40} tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip labelFormatter={(v) => fmtDate(String(v))} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <ReferenceLine y={0} stroke="#94a3b8" />
                  <Line isAnimationActive={false} dataKey="head_difference_m" name="Head difference (m)" stroke="#16a34a" dot={false} strokeWidth={2} />
                  <Line isAnimationActive={false} dataKey="river_level_m" name="River stage (m)" stroke="#0284c7" dot={false} />
                  <Line isAnimationActive={false} dataKey="depth_to_water_m" name="Depth to water (m)" stroke="#7c3aed" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Async>
        </Card>
      </div>
    </>
  );
}
