// Types mirror fast_backend/app/api/schema/*.py — keep both in sync.

export type Status = "good" | "moderate" | "poor" | "critical" | "offline";

export interface Station {
  id: string;
  name: string;
  lat: number;
  lon: number;
  reach: string;
  district: string;
  chainage_km: number;
  telemetry: string;
  installed: string;
}

export interface StationLatest extends Station {
  status: Status;
  health_index: number;
  last_seen: string | null;
  battery_v: number | null;
  signal_dbm: number | null;
  reading: Record<string, number>;
  exceedances: string[];
}

export interface ParameterMeta {
  label: string;
  unit: string;
  min?: number;
  max?: number;
  group: string;
}

export interface ParameterSeries {
  station_id: string;
  parameter: string;
  label: string;
  unit: string;
  limit_min: number | null;
  limit_max: number | null;
  points: { t: string; v: number | null }[];
}

export interface StationForecast {
  station_id: string;
  model: string;
  issued: string;
  days: { date: string; fecal_coliform_mpn: number; category: "Safe" | "Caution" | "Unsafe"; confidence: number }[];
}

export interface Well {
  id: string;
  name: string;
  lat: number;
  lon: number;
  paired_station: string;
  depth_m: number;
  zone: string;
  latest: { depth_to_water_m: number; ec: number; temperature: number };
  river_level_m: number | null;
  head_difference_m: number | null;
  exchange: "gaining" | "losing" | "disconnected" | "unknown";
}

export interface WellSeries {
  well_id: string;
  points: { t: string; depth_to_water_m: number; ec: number; temperature: number; river_level_m: number; head_difference_m: number }[];
}

export interface Alert {
  id: string;
  station_id: string;
  station_name: string;
  parameter: string;
  value: number;
  threshold: number;
  unit: string;
  severity: "critical" | "warning" | "info";
  message: string;
  raised_at: string;
  status: "active" | "acknowledged" | "resolved";
  sampling_triggered: boolean;
}

export interface Waypoint {
  seq: number;
  lat: number;
  lon: number;
  label: string;
  action: "sample" | "measure";
  bottle: number | null;
  status: "done" | "active" | "pending";
}

export interface BoatStatus {
  vessel: string;
  mode: "manual" | "auto";
  state: string;
  lat: number;
  lon: number;
  heading_deg: number;
  speed_mps: number;
  battery_pct: number;
  signal: string;
  gps_fix: string;
  last_update: string;
  mission_id: string;
  mission_name: string;
  waypoints: Waypoint[];
  bottles: { id: number; volume_ml: number; filled: boolean; waypoint: number | null; filled_at: string | null }[];
  track: [number, number][];
  water_quality: Record<string, number>;
}

export interface CommandAck {
  accepted: boolean;
  command: string;
  queued_at: string;
  message: string;
}

export interface Campaign {
  id: string;
  name: string;
  season: string;
  start: string;
  end: string;
  type: "seasonal" | "event";
  trigger: string | null;
  samples: number;
}

export interface Detection {
  compound: string;
  compound_class: string;
  marker_for: string;
  concentration_ng_l: number;
  pnec_ng_l: number;
  risk_quotient: number;
  screening: string;
}

export interface Sample {
  id: string;
  campaign_id: string;
  station_id: string;
  site: string;
  matrix: "water" | "sediment" | "groundwater";
  lat: number;
  lon: number;
  collected_at: string;
  collector: string;
  detections: Detection[];
}

export interface SourceApportionment {
  station_id: string;
  site: string;
  campaign_id: string;
  sources: { source: string; share_pct: number }[];
}

export interface TemTransect {
  id: string;
  name: string;
  survey_date: string;
  length_m: number;
  start: [number, number];
  end: [number, number];
  station: string;
  finding: string;
}

export interface TemSection {
  transect_id: string;
  distances_m: number[];
  depths_m: number[];
  resistivity: number[][];
  interpretation: { label: string; x_from: number; x_to: number; z_from: number; z_to: number; kind: string }[];
}

export interface Survey {
  id: string;
  name: string;
  date: string;
  season: string;
  platform: string;
  area_km2: number;
  gsd_cm: number;
}

export interface Hotspot {
  id: string;
  type: string;
  lat: number;
  lon: number;
  survey: string;
  detail: string;
  severity: "high" | "medium" | "low";
}

export interface CrossSection {
  chainage_km: number;
  location: string;
  offsets_m: number[];
  pre_monsoon_bed_m: number[];
  post_monsoon_bed_m: number[];
  net_change_m2: number;
}

export interface Overview {
  kpi: {
    river_health_index: number;
    rhi_category: Status;
    rhi_change_30d: number;
    stations_online: number;
    stations_total: number;
    active_alerts: number;
    critical_alerts: number;
    samples_this_season: number;
    hotspots: number;
    last_sync: string;
  };
  river_line: [number, number][];
}

export interface HealthHistoryPoint {
  month: string;
  rhi: number;
  by_station: Record<string, number>;
}
