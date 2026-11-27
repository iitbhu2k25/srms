"use client";

import dynamic from "next/dynamic";
import type { MapViewProps } from "./MapView";

// Leaflet touches `window`, so the map is rendered on the client only.
const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => <div className="loading" style={{ height: 420 }}>Loading map…</div>,
});

export default function Map(props: MapViewProps) {
  return <MapView {...props} />;
}

export type { MapMarker, MapLine } from "./MapView";
