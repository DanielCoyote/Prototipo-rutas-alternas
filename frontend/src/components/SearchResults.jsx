import { useState } from 'react';
import './SearchResults.css';

/**
 * Componente que muestra el panel de resultados con las opciones de rutas
 * Permite al usuario ver y seleccionar entre múltiples alternativas
 */
const SearchResults = ({ routes, selectedRouteIndex, onSelectRoute }) => {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  // Si no hay rutas, no mostrar nada
  if (!routes || routes.length === 0) {
    return null;
  }

  // Formatear duración en formato legible
  const formatDuration = (minutes) => {
    if (!minutes) return 'N/A';
    
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

  // Formatear distancia
  const formatDistance = (km) => {
    if (!km) return 'N/A';
    return `${km.toFixed(1)} km`;
  };

  return (
    <div className="search-results-container">
      <div className="search-results-header">
        <h3>Resultados de la Búsqueda</h3>
        <span className="results-count">{routes.length} {routes.length === 1 ? 'ruta' : 'rutas'}</span>
      </div>
      
      <div className="search-results-list">
        {routes.map((route, index) => (
          <div
            key={index}
            className={`route-card ${selectedRouteIndex === index ? 'selected' : ''} ${hoveredIndex === index ? 'hovered' : ''}`}
            onClick={() => onSelectRoute(index)}
            onMouseEnter={() => setHoveredIndex(index)}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <div className="route-card-header">
              <div className="route-number">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4M12 8h.01"/>
                </svg>
                <span className="route-label">Ruta / Dirección {index + 1}</span>
              </div>
              
              <div className="route-card-info">
                <div className="route-info-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 6v6l4 2"/>
                  </svg>
                  <span className="info-value">{formatDuration(route.duration)}</span>
                </div>
                
                <div className="route-info-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                    <circle cx="12" cy="10" r="3"/>
                  </svg>
                  <span className="info-value">{formatDistance(route.distance)}</span>
                </div>
              </div>
              
              {selectedRouteIndex === index && (
                <div className="selected-badge">
                  <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="8" fill="#3B82F6"/>
                    <path d="M5 8L7 10L11 6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchResults;
