import { GeoJSON } from 'react-leaflet';
import { useEffect, useState } from 'react';
import * as turf from '@turf/turf';

// Función para obtener el color según la severidad
function getSeverityColor(severity) {
  switch(severity) {
    case 1: return '#4CAF50'; // Verde - Bajo
    case 2: return '#FFC107'; // Amarillo - Medio
    case 3: return '#F44336'; // Rojo - Crítico
    default: return '#F44336'; // Por defecto: rojo
  }
}

// Función para obtener el nombre de la severidad
function getSeverityName(severity) {
  switch(severity) {
    case 1: return 'Bajo';
    case 2: return 'Medio';
    case 3: return 'Crítico';
    default: return 'Desconocido';
  }
}

export default function PolygonsLayer({ styleOptions }) {
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

  const style = (feature) => {
    const severity = feature.properties?.severity || 3;
    
    return {
      color: '#333',
      weight: 1,
      fillColor: styleOptions?.fillColor || getSeverityColor(severity),
      fillOpacity: styleOptions?.fillOpacity ?? 0.35
    };
  };

  const onEachFeature = (feature, layer) => {
    layer.on('click', (e) => {
      try {
        const pt = turf.point([e.latlng.lng, e.latlng.lat]);
        const overlaps = geojson.features.filter(f => turf.booleanPointInPolygon(pt, f));
        
        if (overlaps.length > 0) {
          const content = overlaps.map(f => {
            const props = f.properties || {};
            const severity = props.severity || 3;
            const severityName = getSeverityName(severity);
            const description = props.description || 'Zona inundable';
            return `
              <strong>Severidad:</strong> ${severityName} (${severity})<br>
              <strong>Descripción:</strong> ${description}<br>
              <strong>Fuente:</strong> ${props.source || 'N/A'}
            `;
          }).join('<hr>');
          
          layer.bindPopup(`<div style="max-width:250px">${content}</div>`).openPopup();
        } else {
          layer.bindPopup('No hay zonas de riesgo en este punto').openPopup();
        }
      } catch (err) {
        console.error('Error computing overlaps', err);
      }
    });
  };

  return <GeoJSON key={JSON.stringify(geojson)} data={geojson} style={style} onEachFeature={onEachFeature} />;
}