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
      <div style={{ padding: "20px", textAlign: "center", color: "#666" }}>
        Cargando historial...
      </div>
    );
  }

  if (routes.length === 0) {
    return (
      <div style={{ padding: "20px", textAlign: "center", color: "#666" }}>
        No hay rutas en el historial
      </div>
    );
  }

  return (
    <div style={{ 
      maxHeight: "400px", 
      overflowY: "auto",
      padding: "10px"
    }}>
      <h3 style={{ 
        margin: "0 0 15px 0", 
        fontSize: "16px", 
        color: "#2D3748",
        padding: "0 10px"
      }}>
        Historial de Rutas (últimas 10)
      </h3>
      
      {routes.map((route) => (
        <div
          key={route.id}
          onClick={() => handleRouteClick(route)}
          style={{
            padding: "12px",
            margin: "8px 0",
            backgroundColor: "white",
            borderRadius: "8px",
            border: "1px solid #E2E8F0",
            cursor: "pointer",
            transition: "all 0.2s",
            position: "relative"
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#F7FAFC";
            e.currentTarget.style.borderColor = "#4FD1C5";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "white";
            e.currentTarget.style.borderColor = "#E2E8F0";
          }}
        >
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between",
            alignItems: "start"
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontSize: "14px", 
                fontWeight: "bold",
                color: "#2D3748",
                marginBottom: "4px"
              }}>
                <span style={{ color: "#48BB78" }}>●</span> {route.origin_label}
              </div>
              <div style={{ 
                fontSize: "14px", 
                fontWeight: "bold",
                color: "#2D3748",
                marginBottom: "8px"
              }}>
                <span style={{ color: "#F56565" }}>📍</span> {route.destination_label}
              </div>
              <div style={{ 
                fontSize: "12px", 
                color: "#718096",
                display: "flex",
                gap: "15px"
              }}>
                <span>⏱️ {formatDuration(route.duration_minutes)}</span>
                {route.distance_km && (
                  <span>📏 {route.distance_km.toFixed(1)} km</span>
                )}
              </div>
            </div>
            
            <button
              onClick={(e) => handleDelete(route.id, e)}
              style={{
                padding: "6px 10px",
                backgroundColor: "#FED7D7",
                color: "#C53030",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: "bold"
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "#FC8181";
                e.currentTarget.style.color = "white";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "#FED7D7";
                e.currentTarget.style.color = "#C53030";
              }}
            >
              🗑️
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
