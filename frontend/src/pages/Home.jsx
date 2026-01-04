import MapView from "../components/MapView";
import SearchBar from "../components/SearchBar/SearchBar";
import SearchResults from "../components/SearchResults";
import { getRoute } from "../services/ors";
import { saveRouteHistory } from "../services/api";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const [routes, setRoutes] = useState(null); // Array de rutas alternativas
  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0); // Índice de ruta seleccionada
  const [originMarker, setOriginMarker] = useState(null);
  const [destinationMarker, setDestinationMarker] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [avoidZones, setAvoidZones] = useState(false);
  const [avoidPolygonsCache, setAvoidPolygonsCache] = useState(null);
  const [externalDestination, setExternalDestination] = useState(null);
  const [lastRouteInfo, setLastRouteInfo] = useState(null);
  
  // Estados para navegación en tiempo real
  const [isNavigating, setIsNavigating] = useState(false);
  const [currentPosition, setCurrentPosition] = useState(null);
  const [currentSpeed, setCurrentSpeed] = useState(0);
  const [currentHeading, setCurrentHeading] = useState(0);
  const [watchId, setWatchId] = useState(null);
  const [lastKnownPosition, setLastKnownPosition] = useState(null);

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/login");
  };

  // Show error banner in UI
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleSearch = async (originObj, destinationObj) => {
    // originObj and destinationObj: { label, coords: [lon, lat] }
    setRoutes(null);
    setSelectedRouteIndex(0);
    setError(null);
    setLoading(true);

    // Markers should be [lat, lon]
    setOriginMarker(originObj.coords ? [originObj.coords[1], originObj.coords[0]] : null);
    setDestinationMarker(destinationObj.coords ? [destinationObj.coords[1], destinationObj.coords[0]] : null);

    let avoid = null;
    if (avoidZones) {
      try {
        // reuse cache if already fetched
        if (!avoidPolygonsCache) {
          const r = await fetch('/api/polygons');
          if (r.ok) {
            avoid = await r.json();
            setAvoidPolygonsCache(avoid);
          } else {
            console.warn('No se pudieron obtener polígonos de evitación');
            setError('No se pudieron obtener polígonos de evitación');
          }
        } else {
          avoid = avoidPolygonsCache;
        }
      } catch (err) {
        console.error('Error loading avoid polygons', err);
        setError('Error al cargar zonas a evitar');
      }
    }

    try {
      const res = await getRoute(originObj.coords, destinationObj.coords, avoid);
      if (res && res.routes && res.routes.length > 0) {
        setRoutes(res.routes);
        
        // Save route info for later (using first/primary route)
        const primaryRoute = res.routes[0];
        setLastRouteInfo({
          origin: originObj,
          destination: destinationObj,
          duration: primaryRoute.duration,
          distance: primaryRoute.distance
        });
        
        // Save primary route to history
        try {
          await saveRouteHistory(
            originObj.label,
            destinationObj.label,
            originObj.coords,
            destinationObj.coords,
            primaryRoute.duration,
            primaryRoute.distance
          );
        } catch (historyError) {
          console.error("Error saving to history:", historyError);
          // Don't show error to user, route was calculated successfully
        }
      } else {
        setRoutes(null);
        setError('No se encontró ruta para las coordenadas proporcionadas');
      }
    } catch (err) {
      console.error("Error fetching route:", err);
      setRoutes(null);
      setError(err?.message || 'Error al obtener la ruta');
    } finally {
      setLoading(false);
    }
  };

  // Handle destination change from favorite marker
  const handleDestinationChange = (coords, label) => {
    // coords comes as [lat, lon] from FavoriteMarkers
    setDestinationMarker(coords);
    // Clear routes when destination changes
    setRoutes(null);
    setSelectedRouteIndex(0);
    
    // Update SearchBar with favorite info
    // coords format received: [lat, lon], need to convert to [lon, lat] for ORS
    setExternalDestination({
      label: label || `${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}`,
      coords: [coords[1], coords[0]] // Convert [lat, lon] -> [lon, lat]
    });
  };

  // Handle route selection (from SearchResults, MapView markers, or route lines)
  const handleRouteSelect = async (index) => {
    if (index === selectedRouteIndex) return; // Ya está seleccionada
    
    setSelectedRouteIndex(index);
    
    // Guardar la ruta recién seleccionada en el historial
    if (routes && routes[index] && lastRouteInfo) {
      try {
        await saveRouteHistory(
          lastRouteInfo.origin.label,
          lastRouteInfo.destination.label,
          lastRouteInfo.origin.coords,
          lastRouteInfo.destination.coords,
          routes[index].duration,
          routes[index].distance
        );
      } catch (historyError) {
        console.error("Error saving selected route to history:", historyError);
      }
    }
  };

  // Handle route selection from history
  const handleRouteFromHistory = (originObj, destinationObj) => {
    handleSearch(originObj, destinationObj);
  };

  // Calcular distancia entre dos puntos en metros
  const calculateDistance = (pos1, pos2) => {
    const R = 6371e3; // Radio de la Tierra en metros
    const φ1 = (pos1[0] * Math.PI) / 180;
    const φ2 = (pos2[0] * Math.PI) / 180;
    const Δφ = ((pos2[0] - pos1[0]) * Math.PI) / 180;
    const Δλ = ((pos2[1] - pos1[1]) * Math.PI) / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  };

  // Función para recalcular la ruta cuando el usuario se desvía
  const recalculateRoute = async (newOrigin) => {
    if (!lastRouteInfo || !lastRouteInfo.destination) {
      console.error("No hay información de destino para recalcular");
      return;
    }

    console.log("Recalculando ruta desde nueva posición...");

    try {
      // Convertir [lat, lon] a [lon, lat] para la API
      const originCoords = [newOrigin[1], newOrigin[0]];
      const destinationCoords = lastRouteInfo.destination.coords;

      let avoid = null;
      if (avoidZones && avoidPolygonsCache) {
        avoid = avoidPolygonsCache;
      }

      const res = await getRoute(originCoords, destinationCoords, avoid);
      
      if (res && res.routes && res.routes.length > 0) {
        setRoutes(res.routes);
        // Mantener la ruta seleccionada en el índice 0 (la nueva ruta principal)
        setSelectedRouteIndex(0);
        
        // Actualizar marcador de origen
        setOriginMarker(newOrigin);
        
        console.log("Ruta recalculada exitosamente");
      }
    } catch (err) {
      console.error("Error recalculando ruta:", err);
      // No detenemos la navegación, solo mostramos el error
    }
  };

  // Función para iniciar la navegación
  const startNavigation = () => {
    if (!routes || routes.length === 0) {
      alert("Primero debes calcular una ruta");
      return;
    }

    if (!navigator.geolocation) {
      alert("Tu navegador no soporta geolocalización");
      return;
    }

    setIsNavigating(true);

    const id = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude, heading, speed } = position.coords;
        const newPos = [latitude, longitude];

        setCurrentPosition(newPos);
        setOriginMarker(newPos);

        // Actualizar velocidad (convertir m/s a km/h)
        if (speed !== null && speed !== undefined) {
          setCurrentSpeed(Math.max(0, speed * 3.6));
        }

        // Actualizar dirección
        if (heading !== null && heading !== undefined) {
          setCurrentHeading(heading);
        }

        // Verificar si nos desviamos de la ruta
        if (routes && routes[selectedRouteIndex] && lastKnownPosition) {
          const selectedRoute = routes[selectedRouteIndex];
          let minDistance = Infinity;

          // Calcular distancia mínima a cualquier punto de la ruta
          selectedRoute.coords.forEach(routePoint => {
            const dist = calculateDistance(newPos, routePoint);
            if (dist < minDistance) {
              minDistance = dist;
            }
          });

          // Si nos desviamos más de 50 metros, recalcular
          if (minDistance > 50 && lastRouteInfo) {
            recalculateRoute(newPos);
          }
        }

        setLastKnownPosition(newPos);
      },
      (error) => {
        console.error('Error de geolocalización:', error);
        if (error.code === error.PERMISSION_DENIED) {
          alert('Permiso de ubicación denegado. Por favor habilita la ubicación para usar la navegación.');
          stopNavigation();
        } else {
          setError('Error al obtener ubicación');
        }
      },
      {
        enableHighAccuracy: true,
        maximumAge: 1000,
        timeout: 10000
      }
    );

    setWatchId(id);
  };

  // Función para detener la navegación
  const stopNavigation = () => {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      setWatchId(null);
    }
    setIsNavigating(false);
    setCurrentSpeed(0);
    setCurrentHeading(0);
    setCurrentPosition(null);
    setLastKnownPosition(null);
  };

  // Cleanup al desmontar componente
  useEffect(() => {
    return () => {
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
      }
    };
  }, [watchId]);

  return (
    <div style={{ height: "100vh", width: "100%", position: "relative" }}>
      <SearchBar 
        onSearch={handleSearch} 
        onLogout={handleLogout}
        externalDestination={externalDestination}
        onRouteFromHistory={handleRouteFromHistory}
        avoidZones={avoidZones}
        setAvoidZones={setAvoidZones}
      />
      
      {/* Indicador de velocidad durante navegación */}
      {isNavigating && (
        <div style={{
          position: "absolute",
          top: "80px",
          right: "20px",
          zIndex: 1001,
          backgroundColor: "white",
          padding: "12px 16px",
          borderRadius: "12px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
          border: "2px solid #3B82F6",
          minWidth: "100px",
          textAlign: "center"
        }}>
          <div style={{
            fontSize: "32px",
            fontWeight: "bold",
            color: "#3B82F6",
            lineHeight: "1"
          }}>
            {Math.round(currentSpeed)}
          </div>
          <div style={{
            fontSize: "14px",
            color: "#666",
            marginTop: "4px"
          }}>
            km/h
          </div>
        </div>
      )}
      
      {/* Panel de resultados de búsqueda */}
      {routes && routes.length > 0 && (
        <div style={{
          position: "absolute",
          bottom: "20px",
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 1000,
          width: "90%",
          maxWidth: "800px"
        }}>
          <SearchResults
            routes={routes}
            selectedRouteIndex={selectedRouteIndex}
            onSelectRoute={handleRouteSelect}
            isNavigating={isNavigating}
            onStartNavigation={startNavigation}
            onStopNavigation={stopNavigation}
          />
        </div>
      )}
      
      <MapView 
        origin={originMarker} 
        destination={destinationMarker} 
        routes={routes}
        selectedRouteIndex={selectedRouteIndex}
        onDestinationChange={handleDestinationChange}
        onRouteSelect={handleRouteSelect}
        isLoading={loading}
        isNavigating={isNavigating}
        currentPosition={currentPosition}
        currentHeading={currentHeading}
        currentSpeed={currentSpeed}
      />
    </div>
  );
}
