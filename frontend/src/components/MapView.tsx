"use client";

import "leaflet/dist/leaflet.css";
import { CircleMarker, GeoJSON, MapContainer, Polyline, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import { useEffect, type ReactNode } from "react";
import type { LatLngBoundsExpression } from "leaflet";

export interface MapMarker {
  id: string;
  lat: number;
  lon: number;
  color: string;
  radius?: number;
  label?: string;
  permanentLabel?: boolean;
  popup?: ReactNode;
  onClick?: () => void;
}

export interface MapLine {
  id: string;
  positions: [number, number][];
  color: string;
  weight?: number;
  dash?: string;
  label?: string;
}

export interface MapGeoJson {
  id: string;
  data: GeoJSON.GeoJsonObject;
  color: string;
  weight?: number;
  fillOpacity?: number;
  dash?: string;
  /** Tooltip text; gets the feature's properties when a function. */
  label?: string | ((props: Record<string, unknown>) => string);
}

export interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  height?: number;
  bounds?: LatLngBoundsExpression;
  river?: [number, number][];
  lines?: MapLine[];
  markers?: MapMarker[];
  /** Vector layers (basin outline, rivers, STP footprints) drawn beneath the markers. */
  geojson?: MapGeoJson[];
  satellite?: boolean;
}

function FitBounds({ bounds }: { bounds?: LatLngBoundsExpression }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [24, 24] });
  }, [map, bounds]);
  return null;
}

export default function MapView({
  center = [25.48, 82.55], zoom = 9, height = 420, bounds, river, lines = [], markers = [], geojson = [], satellite,
}: MapViewProps) {
  return (
    <MapContainer center={center} zoom={zoom} style={{ height, width: "100%" }} scrollWheelZoom>
      {satellite ? (
        <TileLayer
          attribution="Tiles &copy; Esri"
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />
      ) : (
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      )}
      <FitBounds bounds={bounds} />
      {geojson.map((g) => (
        <GeoJSON
          key={g.id}
          data={g.data}
          style={{ color: g.color, weight: g.weight ?? 2, fillOpacity: g.fillOpacity ?? 0, dashArray: g.dash }}
          onEachFeature={(feature, layer) => {
            if (!g.label) return;
            const text = typeof g.label === "function" ? g.label((feature.properties ?? {}) as Record<string, unknown>) : g.label;
            layer.bindTooltip(text, { sticky: true });
          }}
        />
      ))}
      {river && <Polyline positions={river} pathOptions={{ color: "#0284c7", weight: 5, opacity: 0.55 }} />}
      {lines.map((l) => (
        <Polyline key={l.id} positions={l.positions} pathOptions={{ color: l.color, weight: l.weight ?? 3, dashArray: l.dash }}>
          {l.label && <Tooltip sticky>{l.label}</Tooltip>}
        </Polyline>
      ))}
      {markers.map((m) => (
        <CircleMarker
          key={m.id}
          center={[m.lat, m.lon]}
          radius={m.radius ?? 8}
          pathOptions={{ color: "#fff", weight: 2, fillColor: m.color, fillOpacity: 0.95 }}
          eventHandlers={m.onClick ? { click: m.onClick } : undefined}
        >
          {m.label && <Tooltip direction="top" offset={[0, -8]} permanent={m.permanentLabel}>{m.label}</Tooltip>}
          {m.popup && <Popup>{m.popup}</Popup>}
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
