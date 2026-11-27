import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Database, FlaskConical } from "lucide-react";
import { STATUS_COLOR, SEVERITY_COLOR } from "@/lib/colors";
import type { Status } from "@/lib/types";

/** `source="survey"` marks pages built only from the real GIS / survey layers (media/*.shp). */
export function PageHeader({ title, subtitle, actions, source = "dummy" }: {
  title: string; subtitle?: string; actions?: ReactNode; source?: "dummy" | "survey";
}) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="row">
        {actions}
        {source === "survey"
          ? <span className="dummy-banner survey"><Database size={13} /> Survey data</span>
          : <span className="dummy-banner"><FlaskConical size={13} /> Dummy data</span>}
      </div>
    </div>
  );
}

export function Card({ title, sub, actions, children, flush, className }: {
  title?: ReactNode; sub?: ReactNode; actions?: ReactNode; children: ReactNode; flush?: boolean; className?: string;
}) {
  return (
    <section className={`card ${className ?? ""}`}>
      {title && (
        <div className="card-head">
          <h3>{title}</h3>
          {sub && <span className="sub">{sub}</span>}
          <span className="spacer" />
          {actions}
        </div>
      )}
      <div className={`card-body ${flush ? "flush" : ""}`}>{children}</div>
    </section>
  );
}

export function Stat({ label, value, hint, icon: Icon, color = "#0e7490" }: {
  label: string; value: ReactNode; hint?: ReactNode; icon: LucideIcon; color?: string;
}) {
  return (
    <div className="card stat">
      <div className="stat-icon" style={{ background: `${color}18`, color }}><Icon size={18} /></div>
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        {hint && <div className="stat-hint">{hint}</div>}
      </div>
    </div>
  );
}

export function StatusBadge({ status }: { status: Status }) {
  const c = STATUS_COLOR[status];
  return <span className="badge" style={{ background: `${c}1a`, color: c }}><span className="dot" style={{ background: c }} />{status}</span>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const c = SEVERITY_COLOR[severity] ?? "#64748b";
  return <span className="badge" style={{ background: `${c}1a`, color: c }}>{severity}</span>;
}

export function Badge({ children, color = "#475569" }: { children: ReactNode; color?: string }) {
  return <span className="badge" style={{ background: `${color}16`, color }}>{children}</span>;
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return <div className="loading">{label}</div>;
}

export function ErrorState({ error }: { error: unknown }) {
  return (
    <div className="error">
      Could not load data from the SRMS API. Is the backend running (<code>docker compose up -d</code>)?
      <div className="small muted" style={{ marginTop: 6 }}>{error instanceof Error ? error.message : String(error)}</div>
    </div>
  );
}

/** Renders loading / error / content for an SWR result. */
export function Async<T>({ data, error, children }: { data: T | undefined; error: unknown; children: (d: T) => ReactNode }) {
  if (error) return <ErrorState error={error} />;
  if (!data) return <Loading />;
  return <>{children(data)}</>;
}
