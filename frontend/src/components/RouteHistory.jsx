import { useState, useEffect } from "react";
import { getRouteHistory, deleteRouteHistory } from "../services/api";

export default function RouteHistory({ onRouteSelect, onClose }) {
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await getRouteHistory();
      setRoutes(data);
    } catch (error) {
      console.error("Error cargando historial:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (routeId, e) => {
    e.stopPropagation();
    if (confirm("¿Eliminar esta ruta del historial?")) {
      try {
        await deleteRouteHistory(routeId);
        setRoutes(routes.filter(r => r.id !== routeId));
      } catch (error) {
        console.error("Error eliminando ruta:", error);
        alert("Error al eliminar la ruta");
      }
    }
  };

  const handleRouteClick = (route) => {
    onRouteSelect({
      origin: {
        label: route.origin_label,
        coords: route.origin_coords // [lon, lat]
      },
      destination: {
        label: route.destination_label,
        coords: route.destination_coords // [lon, lat]
      }
    });
    if (onClose) onClose();
  };

  const formatDuration = (minutes) => {
    if (!minutes) return "N/A";
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins} min`;
  };

  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center", color: "#718096" }}>
        Cargando historial...
      </div>
    );
  }

  if (routes.length === 0) {
    return (
      <div style={{ 
        padding: "40px 20px", 
        textAlign: "center", 
        color: "#718096",
        fontSize: "14px"
      }}>
        <div style={{ fontSize: "48px", marginBottom: "12px" }}>📜</div>
        No hay rutas en el historial
      </div>
    );
  }

  return (
    <div className="route-history-container">
      {routes.map((route) => (
        <div
          key={route.id}
          onClick={() => handleRouteClick(route)}
          className="route-history-item"
        >
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between",
            alignItems: "start"
          }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ 
                fontSize: "13px", 
                fontWeight: "600",
                color: "#2D3748",
                marginBottom: "6px",
                display: "flex",
                alignItems: "center",
                gap: "6px"
              }}>
                <span style={{ 
                  color: "#48BB78",
                  fontSize: "10px",
                  flexShrink: 0
                }}>●</span>
                <span style={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap"
                }}>{route.origin_label}</span>
              </div>
              <div style={{ 
                fontSize: "13px", 
                fontWeight: "600",
                color: "#2D3748",
                marginBottom: "10px",
                display: "flex",
                alignItems: "center",
                gap: "6px"
              }}>
                <span style={{ 
                  fontSize: "14px",
                  flexShrink: 0
                }}>📍</span>
                <span style={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap"
                }}>{route.destination_label}</span>
              </div>
              <div style={{ 
                fontSize: "11px", 
                color: "#718096",
                display: "flex",
                gap: "12px",
                flexWrap: "wrap"
              }}>
                <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  ⏱️ {formatDuration(route.duration_minutes)}
                </span>
                {route.distance_km && (
                  <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    📏 {route.distance_km.toFixed(1)} km
                  </span>
                )}
              </div>
            </div>
            
            <button
              onClick={(e) => handleDelete(route.id, e)}
              className="route-history-delete-btn"
              title="Eliminar"
            >
              🗑️
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
