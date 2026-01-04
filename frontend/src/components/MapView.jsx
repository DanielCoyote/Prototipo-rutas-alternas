import "leaflet-defaulticon-compatibility";
import "leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css";
import "leaflet/dist/leaflet.css";
import "../styles/map-controls.css";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, ZoomControl } from "react-leaflet";
import { useEffect, useState, useMemo } from "react";
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button } from "@mui/material";
import PolygonsLayer from "./PolygonsLayer";
import FavoriteMarkers from "./FavoriteMarkers";
import LocationButton from "./LocationButton";
import MapStyleSelector from "./MapStyleSelector";
import RouteTimeMarker from "./RouteTimeMarker";
import { createFavorite } from "../services/api";
import L from "leaflet";

function FitBounds({ routes, selectedRouteIndex, origin, destination, isNavigating }) {
  const map = useMap();

  useEffect(() => {
    // No ajustar bounds si estamos navegando
    if (isNavigating) return;
    
    const pts = [];
    
    // Si hay rutas, usar la ruta seleccionada o la primera
    if (routes && routes.length > 0) {
      const routeToFit = routes[selectedRouteIndex] || routes[0];
      if (routeToFit.coords && routeToFit.coords.length) {
        pts.push(...routeToFit.coords);
      }
    }
    
    if (origin) pts.push(origin);
    if (destination) pts.push(destination);

    if (pts.length === 0) return;

    const bounds = pts.map(p => [p[0], p[1]]);
    map.fitBounds(bounds, { padding: [50, 50] });
  }, [map, routes, selectedRouteIndex, origin, destination, isNavigating]);

  return null;
}

// Component to handle map double clicks
function MapClickHandler({ onClick }) {
  const map = useMap();

  useEffect(() => {
    map.on('dblclick', onClick);
    return () => {
      map.off('dblclick', onClick);
    };
  }, [map, onClick]);

  return null;
}

// Component to control map during navigation
function NavigationController({ isNavigating, currentPosition, currentHeading, currentSpeed }) {
  const map = useMap();

  useEffect(() => {
    if (!isNavigating || !currentPosition) return;

    // Centrar mapa en posición actual
    map.setView(currentPosition, map.getZoom(), { animate: true, duration: 0.5 });

    // Ajustar zoom según velocidad
    let targetZoom = 15; // zoom por defecto
    if (currentSpeed > 80) {
      targetZoom = 13; // Más alejado para alta velocidad
    } else if (currentSpeed > 50) {
      targetZoom = 14;
    } else if (currentSpeed > 20) {
      targetZoom = 15;
    } else {
      targetZoom = 16; // Más cerca para baja velocidad
    }

    if (Math.abs(map.getZoom() - targetZoom) > 0.5) {
      map.setZoom(targetZoom, { animate: true });
    }

  }, [map, isNavigating, currentPosition, currentSpeed]);

  return null;
}

// Componente para hacer zoom a favorito
function ZoomToFavorite({ coords, shouldZoom, onZoomComplete }) {
  const map = useMap();

  useEffect(() => {
    if (shouldZoom && coords) {
      map.setView(coords, 16, { animate: true, duration: 1 });
      // Notificar que el zoom se completó
      setTimeout(() => {
        if (onZoomComplete) onZoomComplete();
      }, 1000);
    }
  }, [shouldZoom, coords, map, onZoomComplete]);

  return null;
}

export default function MapView({ 
  origin, 
  destination, 
  routes, 
  selectedRouteIndex = 0,
  onDestinationChange,
  onRouteSelect,
  isLoading = false,
  isNavigating = false,
  currentPosition = null,
  currentHeading = 0,
  currentSpeed = 0
}) {
  const [openDialog, setOpenDialog] = useState(false);
  const [favoriteLabel, setFavoriteLabel] = useState("");
  const [clickedLocation, setClickedLocation] = useState(null);
  const [favoritesKey, setFavoritesKey] = useState(0);
  const [zoomToCoords, setZoomToCoords] = useState(null);
  const [shouldZoom, setShouldZoom] = useState(false);
  const [mapStyle, setMapStyle] = useState({
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; OpenStreetMap contributors'
  });

  const handleMapClick = (e) => {
    setClickedLocation([e.latlng.lat, e.latlng.lng]);
    setOpenDialog(true);
  };

  const handleSaveFavorite = async () => {
    if (!favoriteLabel.trim()) {
      alert("Por favor ingresa un nombre para el lugar");
      return;
    }

    try {
      await createFavorite(favoriteLabel, clickedLocation[0], clickedLocation[1]);
      setOpenDialog(false);
      setFavoriteLabel("");
      setClickedLocation(null);
      // Refresh favorites by changing key
      setFavoritesKey(prev => prev + 1);
    } catch (error) {
      console.error("Error guardando favorito:", error);
      alert("Error al guardar el favorito: " + error.message);
    }
  };

  const handleFavoriteClick = (coords, label) => {
    // Hacer zoom al favorito
    setZoomToCoords(coords);
    setShouldZoom(true);
    
    // Establecer como destino
    if (onDestinationChange) {
      onDestinationChange(coords, label);
    }
  };

  const handleZoomComplete = () => {
    setShouldZoom(false);
  };

  const handleStyleChange = (styleKey, styleData) => {
    setMapStyle({
      url: styleData.url,
      attribution: styleData.attribution
    });
  };

  return (
    <div style={{ height: "100vh", width: "100%", position: "relative" }}>
      {/* Loading Overlay */}
      {isLoading && (
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(0, 0, 0, 0.4)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          zIndex: 1000,
          backdropFilter: "blur(2px)"
        }}>
          <div style={{
            backgroundColor: "white",
            padding: "24px 32px",
            borderRadius: "12px",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "16px"
          }}>
            <div style={{
              width: "48px",
              height: "48px",
              border: "4px solid #E5E7EB",
              borderTop: "4px solid #3B82F6",
              borderRadius: "50%",
              animation: "spin 1s linear infinite"
            }} />
            <p style={{
              margin: 0,
              fontSize: "16px",
              fontWeight: "600",
              color: "#1F2937"
            }}>
              Calculando rutas...
            </p>
          </div>
        </div>
      )}
      
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      
      <MapContainer
        center={[19.357, -99.064]}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
      >
        <ZoomControl position="bottomright" />
        <LocationButton />
        <MapStyleSelector onStyleChange={handleStyleChange} />
        <TileLayer
          key={mapStyle.url}
          url={mapStyle.url}
          attribution={mapStyle.attribution}
        />

        <PolygonsLayer styleOptions={{ fillColor: undefined }} />
        <FavoriteMarkers key={favoritesKey} onFavoriteClick={handleFavoriteClick} />
        <ZoomToFavorite 
          coords={zoomToCoords} 
          shouldZoom={shouldZoom} 
          onZoomComplete={handleZoomComplete}
        />

        <MapClickHandler onClick={handleMapClick} />
        <NavigationController 
          isNavigating={isNavigating}
          currentPosition={currentPosition}
          currentHeading={currentHeading}
          currentSpeed={currentSpeed}
        />

        {origin && (
          <Marker position={origin}>
            <Popup>Origen</Popup>
          </Marker>
        )}

        {destination && (
          <Marker position={destination}>
            <Popup>Destino</Popup>
          </Marker>
        )}

        {/* Marcador de posición actual durante navegación */}
        {isNavigating && currentPosition && (
          <Marker 
            position={currentPosition}
            icon={L.divIcon({
              className: 'custom-arrow-marker',
              html: `
                <div style="
                  transform: rotate(${currentHeading}deg);
                  width: 40px;
                  height: 40px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                ">
                  <svg width="40" height="40" viewBox="0 0 40 40">
                    <circle cx="20" cy="20" r="18" fill="#3B82F6" opacity="0.3" />
                    <circle cx="20" cy="20" r="12" fill="#3B82F6" stroke="white" stroke-width="3" />
                    <path d="M 20 8 L 26 20 L 20 17 L 14 20 Z" fill="white" />
                  </svg>
                </div>
              `,
              iconSize: [40, 40],
              iconAnchor: [20, 20]
            })}
          />
        )}

        {/* Renderizar todas las rutas */}
        {routes && routes.length > 0 && routes.map((route, index) => {
          const isPrimary = index === selectedRouteIndex;
          
          // Durante navegación, solo mostrar la ruta seleccionada
          if (isNavigating && !isPrimary) {
            return null;
          }
          
          const polylineColor = '#3B82F6'; // Azul
          const opacity = isPrimary ? 1.0 : 0.5;
          const weight = isPrimary ? 5 : 4;
          
          return (
            <div key={`route-${index}-${selectedRouteIndex}`}>
              <Polyline
                key={`polyline-${index}-${isPrimary}`}
                positions={route.coords}
                color={polylineColor}
                opacity={opacity}
                weight={weight}
                pathOptions={{
                  color: polylineColor,
                  opacity: opacity,
                  weight: weight
                }}
                eventHandlers={{
                  click: () => {
                    if (onRouteSelect && index !== selectedRouteIndex) {
                      onRouteSelect(index);
                    }
                  },
                  mouseover: (e) => {
                    if (!isPrimary) {
                      e.target.setStyle({ weight: weight + 1 });
                    }
                  },
                  mouseout: (e) => {
                    if (!isPrimary) {
                      e.target.setStyle({ weight: weight });
                    }
                  }
                }}
              />
              
              {/* Marcador de tiempo para cada ruta */}
              <RouteTimeMarker
                routeCoords={route.coords}
                duration={route.duration}
                isPrimary={isPrimary}
                onClick={() => {
                  if (onRouteSelect && index !== selectedRouteIndex) {
                    onRouteSelect(index);
                  }
                }}
              />
            </div>
          );
        })}

        <FitBounds 
          routes={routes} 
          selectedRouteIndex={selectedRouteIndex} 
          origin={origin} 
          destination={destination} 
          isNavigating={isNavigating}
        />
      </MapContainer>

      {/* Dialog for adding favorite */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Agregar Lugar Favorito</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nombre del lugar"
            type="text"
            fullWidth
            variant="outlined"
            value={favoriteLabel}
            onChange={(e) => setFavoriteLabel(e.target.value)}
            placeholder="Ej: Casa, Trabajo, Escuela..."
          />
          {clickedLocation && (
            <p style={{ color: "#666", fontSize: "14px", marginTop: "10px" }}>
              Coordenadas: {clickedLocation[0].toFixed(5)}, {clickedLocation[1].toFixed(5)}
            </p>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)} color="inherit">
            Cancelar
          </Button>
          <Button onClick={handleSaveFavorite} variant="contained" style={{ backgroundColor: "#4FD1C5" }}>
            Guardar
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}
