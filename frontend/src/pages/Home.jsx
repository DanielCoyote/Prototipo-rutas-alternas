import MapView from "../components/MapView";
import SearchBar from "../components/SearchBar/SearchBar";
import { getRoute } from "../services/ors";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const [route, setRoute] = useState(null);
  const [originMarker, setOriginMarker] = useState(null);
  const [destinationMarker, setDestinationMarker] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [avoidZones, setAvoidZones] = useState(false);
  const [avoidPolygonsCache, setAvoidPolygonsCache] = useState(null);

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
    setRoute(null);
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
      if (res && res.coords) {
        setRoute(res.coords);
      } else {
        setRoute(null);
        setError('No se encontró ruta para las coordenadas proporcionadas');
      }
    } catch (err) {
      console.error("Error fetching route:", err);
      setRoute(null);
      setError(err?.message || 'Error al obtener la ruta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: "100vh", width: "100%", position: "relative" }}>
      <SearchBar onSearch={handleSearch} avoidZones={avoidZones} setAvoidZones={setAvoidZones} onLogout={handleLogout} />
      <MapView origin={originMarker} destination={destinationMarker} route={route} />
    </div>
  );
}
