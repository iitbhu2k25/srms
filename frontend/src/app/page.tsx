"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity, AlertTriangle, FlaskConical, Gauge, MapPin } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Map from "@/components/Map";
import { Async, Card, PageHeader, SeverityBadge, Stat, StatusBadge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { STATUS_COLOR, SEVERITY_COLOR, rhiStatus } from "@/lib/colors";
import { fmtNum, timeAgo } from "@/lib/format";
import type { Alert, Hotspot, Overview, StationLatest } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const overview = useApi<Overview>("/overview", { refreshInterval: 60_000 });
  const stations = useApi<StationLatest[]>("/stations", { refreshInterval: 60_000 });
  const alerts = useApi<Alert[]>("/alerts", { refreshInterval: 60_000 });
  const hotspots = useApi<Hotspot[]>("/surveys/hotspots");

  const k = overview.data?.kpi;
  const open = alerts.data?.filter((a) => a.status !== "resolved") ?? [];

  return (
    <>
      <PageHeader
        title="Varuna River — live overview"
        subtitle="IoT stations, alerts, pollution hotspots and River Health Index across the basin, from Phulpur (Prayagraj) to the Ganga confluence at Sarai Mohana."
      />

      <div className="grid g-4" style={{ marginBottom: 16 }}>
        <Stat icon={Gauge} label="River Health Index" color={k ? STATUS_COLOR[k.rhi_category] : undefined}
          value={k ? fmtNum(k.river_health_index) : "—"}
          hint={k && <>{k.rhi_category} · {k.rhi_change_30d >= 0 ? "+" : ""}{k.rhi_change_30d} vs 30 d ago</>} />
        <Stat icon={Activity} label="Stations online" value={k ? `${k.stations_online}/${k.stations_total}` : "—"}
          hint={k && `last sync ${timeAgo(k.last_sync)}`} />
        <Stat icon={AlertTriangle} label="Open alerts" color="#dc2626" value={k?.active_alerts ?? "—"}
          hint={k && `${k.critical_alerts} critical · sampling auto-triggered`} />
        <Stat icon={FlaskConical} label="Samples this season" color="#9333ea" value={k?.samples_this_season ?? "—"}
          hint={k && `${k.hotspots} drone hotspots mapped`} />
      </div>

      <div className="grid g-main">
        <Card title="Monitoring network" sub="click a station for details" flush>
          <Map
            height={460}
            river={overview.data?.river_line}
            markers={[
              ...(hotspots.data ?? []).map((h) => ({
                id: h.id, lat: h.lat, lon: h.lon, radius: 5, color: SEVERITY_COLOR[h.severity],
                label: `${h.type}: ${h.detail}`,
              })),
              ...(stations.data ?? []).map((s) => ({
                id: s.id, lat: s.lat, lon: s.lon, radius: 9, color: STATUS_COLOR[s.status],
                label: `${s.id} · ${s.name} — RHI ${s.health_index}`,
                onClick: () => router.push(`/stations/${s.id}`),
              })),
            ]}
          />
          <div className="map-legend">
            {(["good", "moderate", "poor", "critical", "offline"] as const).map((s) => (
              <span key={s}><span className="dot" style={{ background: STATUS_COLOR[s] }} />{s}</span>
            ))}
            <span><MapPin size={12} /> small dots = drone hotspots</span>
          </div>
        </Card>

        <Card title="Open alerts" sub={`${open.length}`} actions={<Link href="/alerts" className="small" style={{ color: "#0e7490" }}>View all →</Link>} flush>
          <Async data={alerts.data} error={alerts.error}>
            {() => (
              <div className="list" style={{ maxHeight: 460, overflowY: "auto" }}>
                {open.length === 0 && <div className="empty">No open alerts</div>}
                {open.slice(0, 10).map((a) => (
                  <div className="list-item" key={a.id}>
                    <SeverityBadge severity={a.severity} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600 }}>{a.message}</div>
                      <div className="small muted">
                        {a.station_id} {a.station_name} · {a.parameter} {fmtNum(a.value, 2)} {a.unit} · {timeAgo(a.raised_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Async>
        </Card>
      </div>

      <div className="grid g-2" style={{ marginTop: 16 }}>
        <Card title="Health index by station" sub="upstream → confluence">
          <Async data={stations.data} error={stations.error}>
            {(list) => (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={list} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid stroke="#eef1f5" vertical={false} />
                  <XAxis dataKey="id" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => [v, "RHI"]} labelFormatter={(id) => list.find((s) => s.id === id)?.name} />
                  <Bar isAnimationActive={false} dataKey="health_index" radius={[4, 4, 0, 0]}>
                    {list.map((s) => <Cell key={s.id} fill={STATUS_COLOR[rhiStatus(s.health_index)]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </Async>
        </Card>

        <Card title="Latest key readings" flush>
          <Async data={stations.data} error={stations.error}>
            {(list) => (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Station</th><th>Status</th><th className="num">DO</th><th className="num">NH₄</th><th className="num">BOD</th><th className="num">Turb.</th></tr>
                  </thead>
                  <tbody>
                    {list.map((s) => (
                      <tr key={s.id} className="clickable" onClick={() => router.push(`/stations/${s.id}`)}>
                        <td><b>{s.id}</b> <span className="muted">{s.name}</span></td>
                        <td><StatusBadge status={s.status} /></td>
                        {(["do", "ammonium", "bod", "turbidity"] as const).map((p) => (
                          <td key={p} className={`num ${s.exceedances.includes(p) ? "exceed" : ""}`}>{fmtNum(s.reading[p], 2)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Async>
        </Card>
      </div>
    </>
  );
}
