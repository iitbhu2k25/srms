"use client";

import { useState } from "react";
import { FlaskConical } from "lucide-react";
import { Async, Badge, Card, PageHeader, SeverityBadge } from "@/components/ui";
import { useApi } from "@/lib/api";
import { fmtNum, fmtTime } from "@/lib/format";
import type { Alert } from "@/lib/types";

const STATUS_COLORS = { active: "#dc2626", acknowledged: "#ca8a04", resolved: "#16a34a" };

export default function AlertsPage() {
  const [status, setStatus] = useState<string>("");
  const [severity, setSeverity] = useState<string>("");
  const qs = new URLSearchParams({ ...(status && { status }), ...(severity && { severity }) }).toString();
  const { data, error } = useApi<Alert[]>(`/alerts${qs ? `?${qs}` : ""}`, { refreshInterval: 60_000 });

  return (
    <>
      <PageHeader
        title="Alerts"
        subtitle="Threshold rules evaluated on the incoming IoT stream (last 48 h). Critical alerts automatically trigger event-based LC-HRMS sampling."
      />
      <Card
        title="Alert log"
        sub={data ? `${data.length} alerts` : undefined}
        actions={
          <div className="row">
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
            </select>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
        }
        flush
      >
        <Async data={data} error={error}>
          {(list) => (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Raised</th><th>Severity</th><th>Station</th><th>Alert</th><th className="num">Value</th><th className="num">Threshold</th><th>Status</th><th>Sampling</th></tr>
                </thead>
                <tbody>
                  {list.length === 0 && <tr><td colSpan={8} className="empty">No alerts match the filter</td></tr>}
                  {list.map((a) => (
                    <tr key={a.id}>
                      <td className="small">{fmtTime(a.raised_at)}</td>
                      <td><SeverityBadge severity={a.severity} /></td>
                      <td><b>{a.station_id}</b><div className="small muted">{a.station_name}</div></td>
                      <td>{a.message}<div className="small muted mono">{a.parameter}</div></td>
                      <td className="num">{fmtNum(a.value, 2)} <span className="muted small">{a.unit}</span></td>
                      <td className="num muted">{a.threshold}</td>
                      <td><Badge color={STATUS_COLORS[a.status]}>{a.status}</Badge></td>
                      <td>{a.sampling_triggered ? <Badge color="#9333ea"><FlaskConical size={11} /> triggered</Badge> : <span className="muted">—</span>}</td>
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
