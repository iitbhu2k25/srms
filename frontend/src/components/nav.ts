import { Activity, AlertTriangle, FlaskConical, Gauge, Layers, LayoutDashboard, Plane, Ship } from "lucide-react";

export interface NavPage {
  href: string;
  label: string;
  icon: typeof Activity;
  /** Pages with the same group are listed under one heading in the sidebar. */
  group: "Overview" | "Data components";
  /** SRMS component the page belongs to (Technical Document, Part A). */
  component?: string;
}

export const PAGES: NavPage[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, group: "Overview" },
  { href: "/health", label: "River Health Index", icon: Gauge, group: "Overview", component: "2.5" },
  { href: "/alerts", label: "Alerts", icon: AlertTriangle, group: "Overview", component: "2.5" },
  { href: "/stations", label: "IoT Stations", icon: Activity, group: "Data components", component: "2.2" },
  { href: "/boat", label: "SMART-STREAM Boat", icon: Ship, group: "Data components", component: "Part B" },
  { href: "/pollutants", label: "Emerging Pollutants", icon: FlaskConical, group: "Data components", component: "2.4" },
  { href: "/subsurface", label: "TEM & Groundwater", icon: Layers, group: "Data components", component: "2.1" },
  { href: "/surveys", label: "Drone & Bathymetry", icon: Plane, group: "Data components", component: "2.3" },
];

export const NAV_GROUPS = ["Overview", "Data components"] as const;
