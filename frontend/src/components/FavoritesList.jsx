import { useEffect, useState } from "react";
import { getFavorites, deleteFavorite } from "../services/api";

export default function FavoritesList({ onClose, onFavoriteSelect }) {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const data = await getFavorites();
      setFavorites(data);
    } catch (error) {
      console.error("Error cargando favoritos:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (favoriteId) => {
    if (confirm("¿Eliminar este lugar favorito?")) {
      try {
        await deleteFavorite(favoriteId);
        setFavorites(favorites.filter(f => f.id !== favoriteId));
      } catch (error) {
        console.error("Error eliminando favorito:", error);
        alert("Error al eliminar el favorito");
      }
    }
  };

  if (loading) {
    return <div style={{ padding: "20px", textAlign: "center", color: "#718096" }}>Cargando...</div>;
  }

  if (favorites.length === 0) {
    return (
      <div style={{ padding: "40px 20px", textAlign: "center", color: "#718096", fontSize: "14px" }}>
        <div style={{ fontSize: "48px", marginBottom: "12px" }}>⭐</div>
        No tienes lugares favoritos guardados.<br/>
        Haz doble clic en el mapa para agregar uno.
      </div>
    );
  }

  return (
    <div className="route-history-container">
      {favorites.map((favorite) => (
        <div 
          key={favorite.id}
          className="route-history-item"
          onClick={() => {
            if (onFavoriteSelect) {
              onFavoriteSelect([favorite.latitude, favorite.longitude], favorite.label);
            }
          }}
          style={{ cursor: "pointer" }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ 
                fontSize: "13px", 
                fontWeight: "600", 
                color: "#2D3748",
                marginBottom: "6px",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                <span style={{ fontSize: "16px", flexShrink: 0 }}>⭐</span>
                <span style={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap"
                }}>{favorite.label}</span>
              </div>
              <div style={{ fontSize: "11px", color: "#718096", marginLeft: "24px" }}>
                {favorite.latitude.toFixed(5)}, {favorite.longitude.toFixed(5)}
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation(); // Evitar que se active el click del favorito
                handleDelete(favorite.id);
              }}
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
