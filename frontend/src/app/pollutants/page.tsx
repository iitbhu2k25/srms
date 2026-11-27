"use client";

import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Map from "@/components/Map";
import { Async, Badge, Card, PageHeader } from "@/components/ui";
import { useApi } from "@/lib/api";
import { useBasinLayers } from "@/lib/gis";
import { fmtDate, fmtNum } from "@/lib/format";
import type { Campaign, Sample, SourceApportionment } from "@/lib/types";

const SOURCE_COLORS: Record<string, string> = {
  "Domestic sewage": "#b45309",
  "Agricultural runoff": "#65a30d",
  "Industrial effluent": "#7c3aed",
  "Urban stormwater": "#0891b2",
  "Hospital waste": "#db2777",
  "Natural / background": "#94a3b8",
};
const MATRIX_COLOR = { water: "#0284c7", sediment: "#a16207", groundwater: "#7c3aed" };

function rqColor(rq: number) {
  if (rq >= 10) return "#fecaca";
  if (rq >= 1) return "#fed7aa";
  if (rq >= 0.1) return "#fef3c7";
  return "#f1f5f9";
}

export default function PollutantsPage() {
  const campaigns = useApi<Campaign[]>("/lab/campaigns");
  const [cid, setCid] = useState<string>("C-2026-POST");
  const samples = useApi<Sample[]>(`/lab/samples?campaign_id=${cid}`);
  const appo = useApi<SourceApportionment[]>(`/lab/apportionment/${cid}`);
  const basin = useBasinLayers();

  const compounds = useMemo(() => {
    const set: string[] = [];
    samples.data?.forEach((s) => s.detections.forEach((d) => !set.includes(d.compound) && set.push(d.compound)));
    return set;
  }, [samples.data]);

  const appoRows = appo.data?.map((a) => ({ site: a.station_id, name: a.site, ...Object.fromEntries(a.sources.map((s) => [s.source, s.share_pct])) }));

  return (
    <>
      <PageHeader
        title="Emerging pollutants — LC-HRMS fingerprinting"
        subtitle="Target and suspect screening of pharmaceuticals, pesticides, PFAS, hormones and industrial chemicals, with source apportionment. Three seasonal campaigns plus alert-triggered event sampling."
      />

      <Card title="Sampling campaigns" flush>
        <Async data={campaigns.data} error={campaigns.error}>
          {(list) => (
            <table>
              <thead><tr><th>Campaign</th><th>Season</th><th>Type</th><th>Dates</th><th className="num">Samples</th><th /></tr></thead>
              <tbody>
                {list.map((c) => (
                  <tr key={c.id} className="clickable" onClick={() => setCid(c.id)} style={c.id === cid ? { background: "#ecfeff" } : undefined}>
                    <td><b>{c.name}</b><div className="small muted mono">{c.id}</div></td>
                    <td>{c.season}</td>
                    <td>{c.type === "event" ? <Badge color="#dc2626">event</Badge> : <Badge color="#0e7490">seasonal</Badge>}
                      {c.trigger && <div className="small muted">{c.trigger}</div>}</td>
                    <td className="small">{fmtDate(c.start)}{c.end !== c.start && ` – ${fmtDate(c.end)}`}</td>
                    <td className="num">{c.samples}</td>
                    <td>{c.id === cid && <Badge color="#0e7490">selected</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Async>
      </Card>

      <div className="grid g-main" style={{ marginTop: 16 }}>
        <Card title="Source apportionment" sub="share of pollutant load by source, %">
          <Async data={appoRows} error={appo.error}>
            {(rows) => (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={rows} margin={{ top: 4, right: 8, left: -14, bottom: 0 }}>
                  <CartesianGrid stroke="#eef1f5" vertical={false} />
                  <XAxis dataKey="site" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip labelFormatter={(s) => rows.find((r) => r.site === s)?.name} formatter={(v) => `${v}%`} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {Object.entries(SOURCE_COLORS).map(([k, c]) => <Bar key={k} isAnimationActive={false} dataKey={k} stackId="a" fill={c} />)}
                </BarChart>
              </ResponsiveContainer>
            )}
          </Async>
        </Card>
        <Card title="Sample locations" flush>
          <Async data={samples.data} error={samples.error}>
            {(list) => (
              <>
                <Map height={300} geojson={basin} bounds={list.map((s) => [s.lat, s.lon] as [number, number])}
                  markers={list.map((s) => ({
                    id: s.id, lat: s.lat, lon: s.lon, color: MATRIX_COLOR[s.matrix], radius: s.matrix === "water" ? 7 : 6,
                    label: `${s.site} · ${s.matrix} · ${s.detections.length} compounds`,
                  }))} />
                <div className="map-legend">
                  {Object.entries(MATRIX_COLOR).map(([k, c]) => <span key={k}><span className="dot" style={{ background: c }} />{k}</span>)}
                </div>
              </>
            )}
          </Async>
        </Card>
      </div>

      <div style={{ marginTop: 16 }} />
      <Card title="Concentration matrix" sub="ng/L · cell colour = risk quotient (concentration ÷ PNEC)" flush>
        <Async data={samples.data} error={samples.error}>
          {(list) => (
            <>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Sample</th><th>Matrix</th>{compounds.map((c) => <th key={c} className="num">{c}</th>)}</tr>
                  </thead>
                  <tbody>
                    {list.map((s) => {
                      const byName = Object.fromEntries(s.detections.map((d) => [d.compound, d]));
                      return (
                        <tr key={s.id}>
                          <td><b>{s.station_id}</b><div className="small muted">{s.site}</div></td>
                          <td><Badge color={MATRIX_COLOR[s.matrix]}>{s.matrix}</Badge></td>
                          {compounds.map((c) => {
                            const d = byName[c];
                            return (
                              <td key={c} className="num" style={{ background: d ? rqColor(d.risk_quotient) : undefined }}
                                title={d ? `RQ ${d.risk_quotient} · PNEC ${d.pnec_ng_l} ng/L · ${d.screening} screening` : "below detection"}>
                                {d ? fmtNum(d.concentration_ng_l, 1) : <span className="muted">n.d.</span>}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="map-legend">
                <span><span className="dot" style={{ background: "#fecaca" }} />RQ ≥ 10 high risk</span>
                <span><span className="dot" style={{ background: "#fed7aa" }} />1–10 risk</span>
                <span><span className="dot" style={{ background: "#fef3c7" }} />0.1–1 low</span>
                <span>n.d. = not detected</span>
              </div>
            </>
          )}
        </Async>
      </Card>
    </>
  );
}
