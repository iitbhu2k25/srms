import type { Status } from "./types";

export const STATUS_COLOR: Record<Status, string> = {
  good: "#16a34a",
  moderate: "#ca8a04",
  poor: "#ea580c",
  critical: "#dc2626",
  offline: "#64748b",
};

export const SEVERITY_COLOR: Record<string, string> = {
  critical: "#dc2626",
  high: "#dc2626",
  warning: "#ea580c",
  medium: "#ea580c",
  info: "#2563eb",
  low: "#ca8a04",
};

export const SERIES_COLORS = ["#2563eb", "#0d9488", "#9333ea", "#ea580c", "#db2777", "#65a30d", "#0891b2", "#a16207"];

export function rhiStatus(rhi: number): Status {
  if (rhi >= 80) return "good";
  if (rhi >= 60) return "moderate";
  if (rhi >= 40) return "poor";
  return "critical";
}

export const TAPPING_COLOR: Record<string, string> = {
  Untapped: "#dc2626",
  Partial: "#f59e0b",
  Tapped: "#16a34a",
};

export const RIVER_COLOR = "#0284c7";
export const BASIN_COLOR = "#0e7490";
export const STP_COLOR = "#7c3aed";
