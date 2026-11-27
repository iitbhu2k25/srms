"use client";

import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Factory, Gauge, Waves, Workflow } from "lucide-react";
import Map, { type MapGeoJson } from "@/components/Map";
import { Async, Badge, Card, PageHeader, Stat } from "@/components/ui";
import { useApi } from "@/lib/api";
import { STP_COLOR, TAPPING_COLOR } from "@/lib/colors";
import { fmtNum } from "@/lib/format";
import { useBasinLayers } from "@/lib/gis";
import type { Drain, DrainSummary, Stp } from "@/lib/types";

const TAPPING = ["Untapped", "Partial", "Tapped"] as const;
const QUALITY = [
  { key: "bod", label: "BOD" },
  { key: "cod", label: "COD" },
  { key: "tss", label: "TSS" },
  { key: "fc", label: "FC" },
] as const;

/** Marker radius from discharge (MLD), square-root scaled; unknown discharge gets a small dot. */
const radius = (q: number | null) => (q == null ? 3 : Math.min(14, 3 + Math.sqrt(q) * 1.3));

export default function DrainsPage() {
  const summary = useApi<DrainSummary[]>("/gis/drains/summary");
  const drains = useApi<Drain[]>("/gis/drains");
  const stps = useApi<Stp[]>("/gis/stps");
  const basin = useBasinLayers();
  const [river, setRiver] = useState("Varuna");
  const [tapping, setTapping] = useState<string>("");

  const shown = useMemo(
    () => (drains.data ?? []).filter((d) => (!river || d.river_name === river) && (!tapping || d.tapping_status === tapping)),
    [drains.data, river, tapping],
  );
  const stpLayer: MapGeoJson[] = (stps.data ?? []).map((s) => ({
    id: `stp${s.stp_code}`, data: { type: "Feature", geometry: s.footprint, properties: {} } as GeoJSON.Feature,
    color: STP_COLOR, weight: 2, fillOpacity: 0.35, label: s.name,
  }));

  const sum = summary.data ?? [];
  const varuna = sum.find((r) => r.river_name === "Varuna");
  const totalDrains = sum.reduce((a, r) => a + r.drains, 0);
  const cap = (stps.data ?? []).reduce((a, s) => a + (s.capacity_mld ?? 0), 0);
  const used = (stps.data ?? []).reduce((a, s) => a + (s.utilized_mld ?? 0), 0);
  const overloaded = (stps.data ?? []).filter((s) => s.overloaded).length;
  const biggest = shown.filter((d) => d.tapping_status !== "Tapped" && d.discharge != null)
    .sort((a, b) => (b.discharge ?? 0) - (a.discharge ?? 0)).slice(0, 12);

  return (
    <>
      <PageHeader
        title="Drains & sewage treatment plants"
        subtitle="Drain outfall survey and STP inventory from the basin GIS layers (media/Drains, media/STP). Untapped drains discharge untreated wastewater to the river."
        source="survey"
      />

      <div className="grid g-4" style={{ marginBottom: 16 }}>
        <Stat icon={Workflow} label="Drains surveyed" value={totalDrains || "—"} hint={`${sum.length} rivers`} />
        <Stat icon={Waves} label="Untapped Varuna drains" color={TAPPING_COLOR.Untapped}
          value={varuna ? `${varuna.untapped + varuna.partial}/${varuna.drains}` : "—"}
          hint={varuna && `${fmtNum(varuna.discharge_untreated, 0)} MLD surveyed discharge`} />
        <Stat icon={Factory} label="STP capacity" color={STP_COLOR} value={cap ? `${fmtNum(cap, 0)} MLD` : "—"}
          hint={cap ? `${fmtNum(used, 0)} MLD treated (${Math.round((used / cap) * 100)}%)` : undefined} />
        <Stat icon={Gauge} label="Overloaded STPs" color="#ea580c" value={stps.data ? `${overloaded}/${stps.data.length}` : "—"}
          hint="utilisation above design capacity" />
      </div>

      <div className="grid g-main">
        <Card
          title="Drain outfalls & STPs"
          sub={`${shown.length} drains`}
          actions={
            <div className="row">
              <select value={river} onChange={(e) => setRiver(e.target.value)}>
                <option value="">All rivers</option>
                {sum.map((r) => <option key={r.river_name} value={r.river_name}>{r.river_name} ({r.drains})</option>)}
              </select>
              <select value={tapping} onChange={(e) => setTapping(e.target.value)}>
                <option value="">All statuses</option>
                {TAPPING.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          }
          flush
        >
          <Map
            height={480}
            geojson={[...basin, ...stpLayer]}
            bounds={shown.length ? shown.map((d) => [d.lat, d.lon] as [number, number]) : undefined}
            markers={[
              ...shown.map((d) => ({
                id: `d${d.drain_code}`, lat: d.lat, lon: d.lon, radius: radius(d.discharge), color: TAPPING_COLOR[d.tapping_status],
                label: `Drain ${d.drain_code}${d.name ? ` · ${d.name}` : ""} (${d.river_name}) — ${d.tapping_status}${d.discharge != null ? `, ${d.discharge} MLD` : ", discharge not surveyed"}`,
              })),
              ...(stps.data ?? []).map((s) => ({
                id: `s${s.stp_code}`, lat: s.lat, lon: s.lon, radius: 7, color: STP_COLOR,
                label: `${s.name} — ${s.utilization_pct ?? "?"}% utilised${s.overloaded ? " (overloaded)" : ""}`,
              })),
            ]}
          />
          <div className="map-legend">
            {TAPPING.map((t) => <span key={t}><span className="dot" style={{ background: TAPPING_COLOR[t] }} />{t} drain</span>)}
            <span><span className="dot" style={{ background: STP_COLOR }} />STP</span>
            <span>dot size = discharge</span>
          </div>
        </Card>

        <Card title="Drains by river" sub="tapping status">
          <Async data={summary.data} error={summary.error}>
            {(rows) => (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 12, left: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#eef1f5" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="river_name" width={60} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {TAPPING.map((t) => (
                    <Bar key={t} isAnimationActive={false} dataKey={t.toLowerCase()} name={t} stackId="a" fill={TAPPING_COLOR[t]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            )}
          </Async>
          <div className="small muted">
            Discharge is surveyed for {varuna?.with_discharge ?? "—"} of {varuna?.drains ?? "—"} Varuna drains; the rest are shown as small dots.
          </div>
        </Card>
      </div>

      <div style={{ marginTop: 16 }} />
      <Card title="Sewage treatment plants" sub="effluent: actual vs design (mg/L; FC in MPN/100 mL) — orange = exceeds design" flush>
        <Async data={stps.data} error={stps.error}>
          {(list) => (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>STP</th><th>River · district</th><th>Status</th><th className="num">Capacity</th><th style={{ minWidth: 150 }}>Utilisation</th>
                    {QUALITY.map((q) => <th key={q.key} className="num">{q.label}</th>)}
                    <th className="num">pH</th><th className="num">Tapped drains</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((s) => (
                    <tr key={s.stp_code}>
                      <td><b>{s.name}</b><div className="small muted">{s.maintained_by} · {s.stp_type}</div></td>
                      <td className="small">{s.river_name}<div className="muted">{s.district}</div></td>
                      <td><Badge color={s.status === "Compliant" ? "#16a34a" : "#dc2626"}>{s.status ?? "—"}</Badge></td>
                      <td className="num">{fmtNum(s.capacity_mld)} MLD</td>
                      <td>
                        <div className="row" style={{ flexWrap: "nowrap" }}>
                          <div className="bar" style={{ flex: 1 }}>
                            <span style={{ width: `${Math.min(100, s.utilization_pct ?? 0)}%`, background: s.overloaded ? "#dc2626" : "#16a34a" }} />
                          </div>
                          <b className="small" style={{ width: 44, textAlign: "right", color: s.overloaded ? "#dc2626" : undefined }}>
                            {s.utilization_pct == null ? "—" : `${Math.round(s.utilization_pct)}%`}
                          </b>
                        </div>
                      </td>
                      {QUALITY.map((q) => {
                        const a = s[`${q.key}_actual`], d = s[`${q.key}_design`];
                        return (
                          <td key={q.key} className={`num ${s.exceedances.includes(q.key) ? "exceed" : ""}`}>
                            {a == null ? <span className="muted">n.r.</span> : fmtNum(a)}<span className="muted small"> / {d == null ? "—" : fmtNum(d)}</span>
                          </td>
                        );
                      })}
                      <td className={`num ${s.exceedances.includes("ph") ? "exceed" : ""}`}>{s.ph_actual ?? <span className="muted">n.r.</span>}</td>
                      <td className="num">{s.tapped_drains.length || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="map-legend"><span>n.r. = not reported (0 in the source data)</span></div>
            </div>
          )}
        </Async>
      </Card>

      <div style={{ marginTop: 16 }} />
      <Card title="Largest untreated outfalls" sub={river ? `${river} · untapped & partial, by surveyed discharge` : "all rivers"} flush>
        <table>
          <thead><tr><th>Drain</th><th>River</th><th>Status</th><th className="num">Discharge</th><th className="num">Elevation</th><th>Location</th></tr></thead>
          <tbody>
            {biggest.length === 0 && <tr><td colSpan={6} className="empty">No untreated drains with surveyed discharge for this filter</td></tr>}
            {biggest.map((d) => (
              <tr key={d.drain_code}>
                <td><b>Drain {d.drain_code}</b>{d.name && <div className="small muted">{d.name}</div>}</td>
                <td>{d.river_name}</td>
                <td><Badge color={TAPPING_COLOR[d.tapping_status]}>{d.tapping_status}</Badge></td>
                <td className="num"><b>{d.discharge}</b> <span className="muted small">MLD</span></td>
                <td className="num">{d.elevation_m == null ? "—" : `${d.elevation_m} m`}</td>
                <td className="mono">{d.lat.toFixed(4)}, {d.lon.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
