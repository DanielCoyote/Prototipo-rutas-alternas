import { Marker, Popup, useMap } from "react-leaflet";
import { useEffect, useState } from "react";
import { Icon } from "leaflet";
import { getFavorites, deleteFavorite } from "../services/api";

// Icono personalizado para favoritos
const favoriteIcon = new Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default function FavoriteMarkers({ onFavoriteClick }) {
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

  const handleUseAsDestination = (favorite) => {
    if (onFavoriteClick) {
      onFavoriteClick([favorite.latitude, favorite.longitude], favorite.label);
    }
    // Close the popup after selection
    // Note: Leaflet doesn't provide direct popup close in this context
  };

  if (loading) return null;

  return (
    <>
      {favorites.map((favorite) => (
        <Marker
          key={favorite.id}
          position={[favorite.latitude, favorite.longitude]}
          icon={favoriteIcon}
        >
          <Popup>
            <div style={{ minWidth: "200px" }}>
              <h3 style={{ margin: "0 0 10px 0", color: "#2D3748" }}>{favorite.label}</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <button
                  onClick={() => handleUseAsDestination(favorite)}
                  style={{
                    padding: "8px 16px",
                    backgroundColor: "#4FD1C5",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontWeight: "bold"
                  }}
                >
                  Usar como destino
                </button>
                <button
                  onClick={() => handleDelete(favorite.id)}
                  style={{
                    padding: "8px 16px",
                    backgroundColor: "#F56565",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontWeight: "bold"
                  }}
                >
                  Eliminar
                </button>
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
}
