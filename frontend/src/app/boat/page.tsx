"use client";

import { useState } from "react";
import { Battery, Compass, Gauge, Home, Navigation, Pause, Play, Satellite, TestTube, Wifi } from "lucide-react";
import Map from "@/components/Map";
import { Async, Badge, Card, PageHeader, Stat } from "@/components/ui";
import { sendApi, useApi } from "@/lib/api";
import { useBasinLayers } from "@/lib/gis";
import { fmtNum, fmtTime } from "@/lib/format";
import type { BoatStatus, CommandAck } from "@/lib/types";

const WP_COLOR = { done: "#16a34a", active: "#f59e0b", pending: "#94a3b8" };
const WQ_LABEL: Record<string, [string, string]> = {
  ph: ["pH", ""], do: ["DO", "mg/L"], ec: ["EC", "µS/cm"], turbidity: ["Turbidity", "NTU"], temperature: ["Temp", "°C"], orp: ["ORP", "mV"],
};

export default function BoatPage() {
  const { data, error } = useApi<BoatStatus>("/boat/status", { refreshInterval: 3000 });
  const rivers = useBasinLayers({ boundary: false, riverWeight: 2 });
  const [log, setLog] = useState<CommandAck[]>([]);
  const [target, setTarget] = useState({ lat: "25.3350", lon: "82.9900" });

  const send = async (body: Record<string, unknown>) => {
    try {
      const ack = await sendApi<CommandAck>("POST", "/boat/command", body);
      setLog((l) => [ack, ...l].slice(0, 8));
    } catch (e) {
      setLog((l) => [{ accepted: false, command: String(body.command), queued_at: new Date().toISOString(), message: String(e) }, ...l]);
    }
  };

  return (
    <>
      <PageHeader
        title="SMART-STREAM autonomous boat"
        subtitle="Digi-NAVI web control, on-board water-quality unit (ESP32) and automated water sampling (Raspberry Pi + relay-driven pump and solenoid valves)."
      />
      <Async data={data} error={error}>
        {(b) => (
          <div className="stack">
            <div className="grid g-4">
              <Stat icon={Navigation} label="State" value={<span style={{ textTransform: "capitalize", fontSize: 20 }}>{b.state}</span>} hint={`${b.mode} mode · ${b.vessel}`} />
              <Stat icon={Battery} label="Battery" color={b.battery_pct < 30 ? "#dc2626" : "#16a34a"} value={`${fmtNum(b.battery_pct)}%`} hint={b.signal} />
              <Stat icon={Gauge} label="Speed" value={`${b.speed_mps} m/s`} hint={<><Compass size={11} /> heading {b.heading_deg}°</>} />
              <Stat icon={Satellite} label="GPS" value={<span style={{ fontSize: 15 }}>{b.lat.toFixed(5)}, {b.lon.toFixed(5)}</span>} hint={b.gps_fix} />
            </div>

            <div className="grid g-main">
              <Card title={b.mission_name} sub={b.mission_id} flush>
                <Map
                  height={440}
                  bounds={b.route.length ? b.route : b.waypoints.map((w) => [w.lat, w.lon] as [number, number])}
                  satellite
                  geojson={rivers}
                  lines={[
                    { id: "plan", positions: b.route, color: "#ffffff", weight: 2, dash: "6 6", label: "Planned route (along the river)" },
                    { id: "track", positions: b.track, color: "#22d3ee", weight: 4, label: "Travelled track" },
                  ]}
                  markers={[
                    ...b.waypoints.map((w) => ({
                      id: `wp${w.seq}`, lat: w.lat, lon: w.lon, color: WP_COLOR[w.status], radius: 7,
                      label: `${w.seq}. ${w.label} — ${w.action}${w.bottle ? ` (bottle ${w.bottle})` : ""}`,
                    })),
                    { id: "boat", lat: b.lat, lon: b.lon, color: "#e11d48", radius: 10, label: `${b.vessel} · ${b.state}`, permanentLabel: true },
                  ]}
                />
                <div className="map-legend">
                  <span><span className="dot" style={{ background: "#e11d48" }} />boat</span>
                  <span><span className="dot" style={{ background: WP_COLOR.done }} />waypoint done</span>
                  <span><span className="dot" style={{ background: WP_COLOR.active }} />next</span>
                  <span><span className="dot" style={{ background: WP_COLOR.pending }} />pending</span>
                  <span className="spacer" />
                  <span>updated {fmtTime(b.last_update)}</span>
                </div>
              </Card>

              <div className="stack">
                <Card title="Remote control" sub="simulation">
                  <div className="row" style={{ marginBottom: 10 }}>
                    <button className="btn" onClick={() => send({ command: "pause" })}><Pause size={14} /> Pause</button>
                    <button className="btn" onClick={() => send({ command: "resume" })}><Play size={14} /> Resume</button>
                    <button className="btn danger" onClick={() => send({ command: "return_home" })}><Home size={14} /> Return home</button>
                  </div>
                  <div className="row" style={{ marginBottom: 10 }}>
                    <input type="text" value={target.lat} onChange={(e) => setTarget({ ...target, lat: e.target.value })} style={{ width: 92 }} />
                    <input type="text" value={target.lon} onChange={(e) => setTarget({ ...target, lon: e.target.value })} style={{ width: 92 }} />
                    <button className="btn primary" onClick={() => send({ command: "goto", lat: Number(target.lat), lon: Number(target.lon) })}>
                      <Navigation size={14} /> Go to
                    </button>
                  </div>
                  <div className="row">
                    {[1, 2, 3].map((n) => (
                      <button key={n} className="btn" onClick={() => send({ command: "sample", bottle: n })}><TestTube size={14} /> Sample → B{n}</button>
                    ))}
                  </div>
                  {log.length > 0 && (
                    <div style={{ marginTop: 12, borderTop: "1px solid var(--border)", paddingTop: 8 }}>
                      {log.map((l, i) => (
                        <div key={i} className="small" style={{ color: l.accepted ? "#0f766e" : "#b91c1c", marginBottom: 3 }}>
                          {new Date(l.queued_at).toLocaleTimeString("en-IN")} — {l.message}
                        </div>
                      ))}
                    </div>
                  )}
                </Card>

                <Card title="Sample bottles">
                  <div className="grid g-3">
                    {b.bottles.map((bt) => (
                      <div key={bt.id} className="tile" style={{ textAlign: "center" }}>
                        <TestTube size={26} color={bt.filled ? "#0284c7" : "#cbd5e1"} />
                        <div style={{ fontWeight: 600 }}>Bottle {bt.id}</div>
                        <div className="small muted">{bt.volume_ml} mL · WP {bt.waypoint}</div>
                        <Badge color={bt.filled ? "#0284c7" : "#94a3b8"}>{bt.filled ? "filled" : "empty"}</Badge>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card title="On-board water quality" sub={<><Wifi size={11} /> live</>}>
                  <div className="tiles">
                    {Object.entries(b.water_quality).map(([k, v]) => (
                      <div key={k} className="tile">
                        <div className="t-label">{WQ_LABEL[k]?.[0] ?? k}</div>
                        <div className="t-value">{fmtNum(v, 2)}<span className="t-unit">{WQ_LABEL[k]?.[1]}</span></div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>

            <Card title="Mission waypoints" flush>
              <table>
                <thead><tr><th>#</th><th>Location</th><th>Action</th><th>Bottle</th><th>Coordinates</th><th>Status</th></tr></thead>
                <tbody>
                  {b.waypoints.map((w) => (
                    <tr key={w.seq}>
                      <td>{w.seq}</td><td>{w.label}</td><td style={{ textTransform: "capitalize" }}>{w.action}</td>
                      <td>{w.bottle ?? "—"}</td><td className="mono">{w.lat.toFixed(4)}, {w.lon.toFixed(4)}</td>
                      <td><Badge color={WP_COLOR[w.status]}>{w.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </div>
        )}
      </Async>
    </>
  );
}
