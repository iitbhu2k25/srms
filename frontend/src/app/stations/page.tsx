"use client";

import { useRouter } from "next/navigation";
import { Async, Card, PageHeader, StatusBadge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { fmtNum, timeAgo } from "@/lib/format";
import type { ParameterMeta, StationLatest } from "@/lib/types";

const COLS = ["ph", "do", "ec", "turbidity", "temperature", "ammonium", "nitrate", "bod", "water_level", "flow"];

export default function StationsPage() {
  const router = useRouter();
  const { data, error } = useApi<StationLatest[]>("/stations", { refreshInterval: 60_000 });
  const params = useApi<Record<string, ParameterMeta>>("/parameters");

  return (
    <>
      <PageHeader
        title="IoT monitoring stations"
        subtitle="Solar-powered multiparameter stations reporting every 15 minutes over GSM / LoRaWAN / NB-IoT. Values in orange exceed the permissible limit."
      />
      <Card title="All stations" sub={data ? `${data.length} stations` : undefined} flush>
        <Async data={data} error={error}>
          {(list) => (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Station</th><th>Reach</th><th>Status</th><th className="num">RHI</th>
                    {COLS.map((c) => (
                      <th key={c} className="num" title={params.data?.[c]?.label}>
                        {params.data?.[c]?.label.split(" (")[0] ?? c}
                        {params.data?.[c]?.unit && <div style={{ textTransform: "none", fontWeight: 400 }}>{params.data[c].unit}</div>}
                      </th>
                    ))}
                    <th>Last seen</th><th>Link</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((s) => (
                    <tr key={s.id} className="clickable" onClick={() => router.push(`/stations/${s.id}`)}>
                      <td><b>{s.id}</b><div className="small muted">{s.name}</div></td>
                      <td className="small">{s.reach}<div className="muted">km {s.chainage_km}</div></td>
                      <td><StatusBadge status={s.status} /></td>
                      <td className="num"><b>{fmtNum(s.health_index)}</b></td>
                      {COLS.map((c) => (
                        <td key={c} className={`num ${s.exceedances.includes(c) ? "exceed" : ""}`}>{fmtNum(s.reading[c], 2)}</td>
                      ))}
                      <td className="small">{timeAgo(s.last_seen)}</td>
                      <td className="small muted">{s.telemetry}<div>{fmtNum(s.battery_v, 2)} V</div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Async>
      </Card>
    </>
  );
}
