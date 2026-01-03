import { Marker } from 'react-leaflet';
import L from 'leaflet';
import { useMemo } from 'react';

/**
 * Componente que muestra un marcador custom con el tiempo estimado de la ruta
 * Calcula el punto medio de la ruta y muestra el tiempo de llegada
 */
const RouteTimeMarker = ({ routeCoords, duration, isPrimary, onClick }) => {
  // Calcular el punto medio de la ruta
  const midPoint = useMemo(() => {
    if (!routeCoords || routeCoords.length === 0) return null;
    
    const midIndex = Math.floor(routeCoords.length / 2);
    return routeCoords[midIndex];
  }, [routeCoords]);

  // Formatear la duración en formato legible (ej: "15 min", "1 h 30 min")
  const formatDuration = (minutes) => {
    if (!minutes) return '';
    
    if (minutes < 60) {
      return `${Math.round(minutes)} min`;
    }
    
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    
    if (mins === 0) {
      return `${hours} h`;
    }
    
    return `${hours} h ${mins} min`;
  };

  // Crear el icono custom con DivIcon
  const timeIcon = useMemo(() => {
    const durationText = formatDuration(duration);
    
    // Estilos diferentes para ruta primaria y alternativas
    const backgroundColor = isPrimary ? '#FFFFFF' : 'rgba(255, 255, 255, 0.85)';
    const textColor = isPrimary ? '#3B82F6' : 'rgba(59, 130, 246, 0.7)';
    const borderColor = isPrimary ? '#3B82F6' : 'rgba(59, 130, 246, 0.5)';
    const fontWeight = isPrimary ? '600' : '500';
    const boxShadow = isPrimary 
      ? '0 2px 6px rgba(0, 0, 0, 0.3)' 
      : '0 1px 4px rgba(0, 0, 0, 0.2)';

    return L.divIcon({
      className: 'route-time-marker',
      html: `
        <div style="
          background-color: ${backgroundColor};
          color: ${textColor};
          padding: 6px 8px;
          border-radius: 16px;
          border: 2px solid ${borderColor};
          white-space: nowrap;
          box-shadow: ${boxShadow};
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          min-width: 110px;
        " 
        onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 3px 8px rgba(0, 0, 0, 0.4)';"
        onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='${boxShadow}';"
        >
          <div style="
            font-size: 10px;
            font-weight: 500;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          ">
            Tiempo estimado
          </div>
          <div style="
            font-size: 15px;
            font-weight: ${fontWeight};
            line-height: 1;
          ">
            ${durationText}
          </div>
        </div>
      `,
      iconSize: [0, 0], // Tamaño automático basado en contenido
      iconAnchor: [0, 0], // Sin ancla específica, centrado por CSS
    });
  }, [duration, isPrimary]);

  if (!midPoint || !duration) return null;

  return (
    <Marker
      position={midPoint}
      icon={timeIcon}
      eventHandlers={{
        click: onClick,
      }}
    />
  );
};

export default RouteTimeMarker;
