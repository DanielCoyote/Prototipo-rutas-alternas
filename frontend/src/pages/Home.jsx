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
      />
    </div>
  );
}
