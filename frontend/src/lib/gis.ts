import type { MapGeoJson } from "@/components/Map";
import { useApi } from "./api";
import { BASIN_COLOR, RIVER_COLOR } from "./colors";

/** Basin outline + rivers (Varuna, Morwa, Basuhi) from the shapefiles, ready for <Map geojson={...} />. */
export function useBasinLayers({ boundary = true, riverWeight = 3 }: { boundary?: boolean; riverWeight?: number } = {}): MapGeoJson[] {
  const basin = useApi<GeoJSON.Feature>(boundary ? "/gis/boundary" : null);
  const rivers = useApi<GeoJSON.FeatureCollection>("/gis/rivers");
  const layers: MapGeoJson[] = [];
  if (basin.data) {
    layers.push({ id: "basin", data: basin.data, color: BASIN_COLOR, weight: 1.5, dash: "6 5", fillOpacity: 0.04, label: "Varuna basin" });
  }
  if (rivers.data) {
    layers.push({
      id: "rivers", data: rivers.data, color: RIVER_COLOR, weight: riverWeight,
      label: (p) => `${p.name} · ${p.length_km} km`,
    });
  }
  return layers;
}
