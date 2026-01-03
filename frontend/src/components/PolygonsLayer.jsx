import { GeoJSON } from 'react-leaflet';
import { useEffect, useState } from 'react';
import * as turf from '@turf/turf';

export default function PolygonsLayer({ styleOptions }) {
  // allow external styling (e.g., highlight avoided zones)
  const [geojson, setGeojson] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/polygons');
        if (!res.ok) {
          const body = await res.text();
          console.error('Failed to load polygons', res.status, body);
          setError('No se pudieron cargar polígonos');
          return;
        }
        const data = await res.json();
        setGeojson(data);
      } catch (err) {
        console.error('Network error loading polygons', err);
        setError('Error de red al cargar polígonos');
      }
    }
    load();
  }, []);

  if (!geojson) return null;


  const style = (feature) => ({
    color: '#333',
    weight: 1,
    fillColor: styleOptions?.fillColor || feature.properties?.color || '#f03',
    fillOpacity: styleOptions?.fillOpacity ?? 0.35
  });

  const onEachFeature = (feature, layer) => {
    layer.on('click', (e) => {
      try {
        const pt = turf.point([e.latlng.lng, e.latlng.lat]);
        const overlaps = geojson.features.filter(f => turf.booleanPointInPolygon(pt, f));
        const names = overlaps.map(f => f.properties?.name || f.properties?.id || 'sin nombre');
        const content = names.length ? names.join('\n') : 'No hay polígonos en este punto';
        layer.bindPopup(`<pre style="white-space:pre-wrap">${content}</pre>`).openPopup();
      } catch (err) {
        console.error('Error computing overlaps', err);
      }
    });
  };

  return <GeoJSON data={geojson} style={style} onEachFeature={onEachFeature} />;
}