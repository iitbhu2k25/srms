"use client";

import Link from "next/link";
import { use, useMemo, useState } from "react";
import { ArrowLeft, BatteryMedium, Radio } from "lucide-react";
import Map from "@/components/Map";
import TimeSeriesChart from "@/components/charts";
import { Async, Badge, Card, PageHeader, StatusBadge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { STATUS_COLOR } from "@/lib/colors";
import { fmtDate, fmtNum, fmtTime } from "@/lib/format";
import type { ParameterMeta, ParameterSeries, StationForecast, StationLatest } from "@/lib/types";

const RANGES = [
  { label: "24 h", hours: 24 },
  { label: "3 d", hours: 72 },
  { label: "7 d", hours: 168 },
  { label: "30 d", hours: 720 },
  { label: "90 d", hours: 2160 },
];
const QUICK = ["do", "ph", "turbidity", "ec", "ammonium", "nitrate", "bod", "temperature", "water_level", "flow", "rainfall"];
const FC_COLOR = { Safe: "#16a34a", Caution: "#ca8a04", Unsafe: "#dc2626" };

export default function StationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [hours, setHours] = useState(24);
  const [selected, setSelected] = useState<string[]>(["do"]);

  const station = useApi<StationLatest>(`/stations/${id}`, { refreshInterval: 60_000 });
  const meta = useApi<Record<string, ParameterMeta>>("/parameters");
  const forecast = useApi<StationForecast>(`/stations/${id}/forecast`);
  const series = useApi<ParameterSeries[]>(`/stations/${id}/series?parameters=${selected.join(",")}&hours=${hours}`);

  const groups = useMemo(() => {
    const g: Record<string, string[]> = {};
    Object.entries(meta.data ?? {}).forEach(([k, m]) => (g[m.group] ??= []).push(k));
    return g;
  }, [meta.data]);

  const toggle = (p: string) =>
    setSelected((cur) => (cur.includes(p) ? (cur.length > 1 ? cur.filter((x) => x !== p) : cur) : [...cur, p].slice(-4)));

  const s = station.data;
  return (
    <>
      <Link href="/stations" className="small muted row" style={{ marginBottom: 8 }}><ArrowLeft size={14} /> All stations</Link>
      <PageHeader
        title={s ? `${s.id} · ${s.name}` : id}
        subtitle={s ? `${s.reach} · ${s.district} district · chainage km ${s.chainage_km} · installed ${fmtDate(s.installed)}` : undefined}
        actions={s && <StatusBadge status={s.status} />}
      />

      <Async data={s} error={station.error}>
        {(s) => (
          <div className="stack">
            <div className="grid g-main">
              <Card title="Latest reading" sub={s.last_seen ? fmtTime(s.last_seen) : "no data"}
                actions={<span className="row small muted"><BatteryMedium size={14} />{fmtNum(s.battery_v, 2)} V <Radio size={14} />{fmtNum(s.signal_dbm, 0)} dBm · {s.telemetry}</span>}>
                {Object.entries(groups).map(([group, keys]) => (
                  <div key={group} style={{ marginBottom: 12 }}>
                    <div className="small muted" style={{ marginBottom: 6, fontWeight: 600 }}>{group}</div>
                    <div className="tiles">
                      {keys.map((k) => (
                        <div key={k} className={`tile ${s.exceedances.includes(k) ? "bad" : ""}`}>
                          <div className="t-label">{meta.data?.[k].label}</div>
                          <div className="t-value">{fmtNum(s.reading[k], 2)}<span className="t-unit">{meta.data?.[k].unit}</span></div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </Card>

              <div className="stack">
                <Card title="River Health Index">
                  <div className="row" style={{ alignItems: "baseline" }}>
                    <span style={{ fontSize: 36, fontWeight: 700, color: STATUS_COLOR[s.status] }}>{fmtNum(s.health_index)}</span>
                    <span className="muted">/ 100</span>
                  </div>
                  <div className="bar" style={{ marginTop: 8 }}>
                    <span style={{ width: `${s.health_index}%`, background: STATUS_COLOR[s.status] }} />
                  </div>
                  <div className="small muted" style={{ marginTop: 8 }}>
                    {s.exceedances.length ? `${s.exceedances.length} parameters outside limits` : "All parameters within limits"}
                  </div>
                </Card>
                <Card title="Bacterial forecast" sub="faecal coliform, MPN/100 mL">
                  <Async data={forecast.data} error={forecast.error}>
                    {(f) => (
                      <>
                        <div className="grid g-3">
                          {f.days.map((d) => (
                            <div key={d.date} className="tile">
                              <div className="t-label">{new Date(d.date).toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short" })}</div>
                              <div className="t-value" style={{ fontSize: 15 }}>{d.fecal_coliform_mpn.toLocaleString("en-IN")}</div>
                              <Badge color={FC_COLOR[d.category]}>{d.category}</Badge>
                            </div>
                          ))}
                        </div>
                        <div className="small muted" style={{ marginTop: 8 }}>{f.model}</div>
                      </>
                    )}
                  </Async>
                </Card>
                <Card flush>
                  <Map height={180} center={[s.lat, s.lon]} zoom={13}
                    markers={[{ id: s.id, lat: s.lat, lon: s.lon, color: STATUS_COLOR[s.status], radius: 10, label: s.name }]} />
                </Card>
              </div>
            </div>

            <Card
              title="Time series"
              sub="select up to 4 parameters"
              actions={<div className="row">{RANGES.map((r) => (
                <button key={r.hours} className={`chip ${hours === r.hours ? "on" : ""}`} onClick={() => setHours(r.hours)}>{r.label}</button>
              ))}</div>}
            >
              <div className="row" style={{ marginBottom: 12 }}>
                {QUICK.map((p) => (
                  <button key={p} className={`chip ${selected.includes(p) ? "on" : ""}`} onClick={() => toggle(p)}>
                    {meta.data?.[p]?.label ?? p}
                  </button>
                ))}
              </div>
              <Async data={series.data} error={series.error}>
                {(list) =>
                  list.length === 1 ? (
                    <TimeSeriesChart height={300} series={[{ key: list[0].parameter, label: list[0].label, unit: list[0].unit, points: list[0].points, limitMin: list[0].limit_min, limitMax: list[0].limit_max }]} />
                  ) : (
                    <div className="grid g-2">
                      {list.map((x) => (
                        <div key={x.parameter}>
                          <div className="small" style={{ fontWeight: 600, marginBottom: 4 }}>{x.label} <span className="muted">{x.unit}</span></div>
                          <TimeSeriesChart height={200} series={[{ key: x.parameter, label: x.label, unit: x.unit, points: x.points, limitMin: x.limit_min, limitMax: x.limit_max }]} />
                        </div>
                      ))}
                    </div>
                  )
                }
              </Async>
            </Card>
          </div>
        )}
      </Async>
    </>
  );
}
