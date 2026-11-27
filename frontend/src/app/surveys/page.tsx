"use client";

import { useState } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Map from "@/components/Map";
import { Async, Badge, Card, PageHeader, SeverityBadge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { useBasinLayers } from "@/lib/gis";
import { fmtDate } from "@/lib/format";
import type { CrossSection, Hotspot, Survey } from "@/lib/types";

const TYPE_COLOR: Record<string, string> = {
  Outfall: "#dc2626", Encroachment: "#7c3aed", "Bank erosion": "#a16207", Siltation: "#ea580c", "Solid waste": "#475569", "Algal bloom": "#16a34a",
};

export default function SurveysPage() {
  const surveys = useApi<Survey[]>("/surveys");
  const hotspots = useApi<Hotspot[]>("/surveys/hotspots");
  const xs = useApi<CrossSection[]>("/surveys/cross-sections");
  const rivers = useBasinLayers({ boundary: false, riverWeight: 4 });
  const [type, setType] = useState<string>("");
  const [xsIdx, setXsIdx] = useState(1);

  const shown = (hotspots.data ?? []).filter((h) => !type || h.type === type);
  const sec = xs.data?.[xsIdx];

  return (
    <>
      <PageHeader
        title="Drone & bathymetric surveys"
        subtitle="Pre- (May) and post-monsoon (October) drone imagery (RGB, multispectral, thermal) and autonomous-boat echo-sounder bathymetry: outfalls, encroachment, erosion and siltation."
      />
      <div className="grid g-2" style={{ marginBottom: 16 }}>
        <Async data={surveys.data} error={surveys.error}>
          {(list) => list.map((s) => (
            <Card key={s.id} title={s.name} sub={fmtDate(s.date)}>
              <dl className="kv">
                <dt>Platform</dt><dd>{s.platform}</dd>
                <dt>Coverage</dt><dd>{s.area_km2} km² · GSD {s.gsd_cm} cm</dd>
                <dt>Hotspots</dt><dd>{hotspots.data?.filter((h) => h.survey === s.id).length ?? "—"}</dd>
              </dl>
            </Card>
          ))}
        </Async>
      </div>

      <div className="grid g-main">
        <Card title="Hotspot map" sub="urban reach"
          actions={<div className="row">
            <button className={`chip ${!type ? "on" : ""}`} onClick={() => setType("")}>All</button>
            {Object.keys(TYPE_COLOR).map((t) => <button key={t} className={`chip ${type === t ? "on" : ""}`} onClick={() => setType(t)}>{t}</button>)}
          </div>} flush>
          <Map height={420} satellite center={[25.345, 82.96]} zoom={12} geojson={rivers}
            markers={shown.map((h) => ({ id: h.id, lat: h.lat, lon: h.lon, color: TYPE_COLOR[h.type] ?? "#334155", radius: 8, label: `${h.type}: ${h.detail}` }))} />
          <div className="map-legend">
            {Object.entries(TYPE_COLOR).map(([k, c]) => <span key={k}><span className="dot" style={{ background: c }} />{k}</span>)}
          </div>
        </Card>
        <Card title="Hotspot inventory" sub={`${shown.length}`} flush>
          <div className="list" style={{ maxHeight: 470, overflowY: "auto" }}>
            {shown.map((h) => (
              <div className="list-item" key={h.id}>
                <span className="dot" style={{ background: TYPE_COLOR[h.type], marginTop: 6 }} />
                <div style={{ flex: 1 }}>
                  <div className="row"><b>{h.type}</b><SeverityBadge severity={h.severity} /><span className="spacer" /><span className="small muted mono">{h.id}</span></div>
                  <div className="small">{h.detail}</div>
                  <div className="small muted">{h.survey === "SV-2026-PRE" ? "Pre-monsoon" : "Post-monsoon"} · {h.lat.toFixed(4)}, {h.lon.toFixed(4)}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div style={{ marginTop: 16 }} />
      <Card title="Bathymetric cross-section — pre vs post monsoon" sub={sec ? `${sec.location} · km ${sec.chainage_km}` : undefined}
        actions={<div className="row">{xs.data?.map((x, i) => (
          <button key={x.chainage_km} className={`chip ${i === xsIdx ? "on" : ""}`} onClick={() => setXsIdx(i)}>km {x.chainage_km}</button>
        ))}</div>}
        >
        <Async data={sec} error={xs.error}>
          {(s) => (
            <>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={s.offsets_m.map((o, i) => ({ o, pre: s.pre_monsoon_bed_m[i], post: s.post_monsoon_bed_m[i] }))} margin={{ top: 8, right: 16, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="#eef1f5" />
                  <XAxis dataKey="o" type="number" domain={["dataMin", "dataMax"]} tick={{ fontSize: 11 }} label={{ value: "offset from centre-line (m)", position: "insideBottom", offset: -2, fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} label={{ value: "bed elevation (m)", angle: -90, position: "insideLeft", offset: 20, fontSize: 11 }} />
                  <Tooltip formatter={(v) => `${v} m`} labelFormatter={(o) => `offset ${o} m`} />
                  <Legend />
                  <Area isAnimationActive={false} dataKey="pre" name="Pre-monsoon bed" stroke="#0284c7" fill="#0284c7" fillOpacity={0.12} />
                  <Line isAnimationActive={false} dataKey="post" name="Post-monsoon bed" stroke="#ea580c" strokeWidth={2} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
              <div className="row small">
                Net change:&nbsp;
                <Badge color={s.net_change_m2 >= 0 ? "#ea580c" : "#0284c7"}>
                  {s.net_change_m2 >= 0 ? "+" : ""}{s.net_change_m2} m² {s.net_change_m2 >= 0 ? "deposition (siltation)" : "scour"}
                </Badge>
              </div>
            </>
          )}
        </Async>
      </Card>
    </>
  );
}
